"""
DSV / DB Schenker public tracking verifier.

The former DB Schenker page now redirects to myDSV. The most reliable public
path we have is to open the public tracking page and parse the visible result,
the same way a user checks one STT manually.
"""
import asyncio
import re
import json
import os
import sys
from datetime import datetime


def parse_api_data(api_data: dict) -> dict:
    """
    从 Schenker API 返回的 JSON 数据解析状态。
    返回 {'status': str, 'delivery_date': str|None, 'raw': str}
    """
    events = api_data.get('events', [])
    progress = api_data.get('progressBar', {})
    active_step = progress.get('activeStep', '')

    # 检查取消：任何事件有 cancel 相关的 reason
    for ev in events:
        reasons = ev.get('reasons', [])
        for reason in reasons:
            desc = reason.get('description', '').lower()
            if 'cancel' in desc:
                return {'status': 'booked_cancelled', 'delivery_date': None, 'raw': f"Booked ({reason.get('description', 'cancelled')})"}

    # 检查已交付：DLV 事件 + activeStep == DELIVERED 双重确认
    # 仅有 DLV 事件不够，中转站到达也会产生 DLV 事件（comment 非 "Delivered"）
    # 必须同时满足 progressBar.activeStep == "DELIVERED" 才是最终交付
    delivered_event = None
    if active_step == 'DELIVERED':
        for ev in reversed(events):
            if ev.get('code') == 'DLV':
                delivered_event = ev
                break

    if delivered_event:
        date_str = delivered_event.get('date', '')
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return {
                    'status': 'delivered',
                    'delivery_date': dt.strftime('%Y-%m-%d'),
                    'raw': f"Delivered {dt.strftime('%Y/%m/%d')}"
                }
            except (ValueError, TypeError):
                pass
        return {'status': 'delivered', 'delivery_date': None, 'raw': 'Delivered (date parse error)'}

    # activeStep == DELIVERED 但没有 DLV 事件，兜底
    if active_step == 'DELIVERED':
        return {'status': 'delivered', 'delivery_date': None, 'raw': 'Delivered (no DLV event)'}
    elif active_step in ('IN_DELIVERY', 'DISPATCHING_CENTER'):
        return {'status': 'in_transport', 'delivery_date': None, 'raw': f'In transit (step: {active_step})'}
    elif active_step == 'TRANSPORTATION':
        return {'status': 'in_transport', 'delivery_date': None, 'raw': 'In transportation'}
    elif active_step == 'BOOKED':
        return {'status': 'booked', 'delivery_date': None, 'raw': 'Booked'}

    # 兜底：按事件判断
    if events:
        last_event = events[-1]
        comment = last_event.get('comment', '').lower()
        if 'delivered' in comment:
            return {'status': 'delivered', 'delivery_date': None, 'raw': f'Delivered (from comment)'}
        if 'not delivered' in comment:
            return {'status': 'in_transport', 'delivery_date': None, 'raw': 'Not delivered (retry)'}

    return {'status': 'unknown', 'delivery_date': None, 'raw': f'Unknown (step: {active_step})'}


def classify_status(page_text: str) -> dict:
    """
    兜底：从页面文本解析状态（当 API 拦截失败时使用）。
    返回 {'status': str, 'delivery_date': str|None, 'raw': str}
    """
    text_lower = page_text.lower()

    if 'captcha' in text_lower or 'too many requests' in text_lower or 'rate limit' in text_lower:
        return {
            'status': 'error',
            'delivery_date': None,
            'raw': 'DSV captcha/rate limit',
            'success': False,
        }

    if 'shipment not found' in text_lower or 'no data found' in text_lower:
        return {'status': 'not_found', 'delivery_date': None, 'raw': 'Shipment not found'}

    if re.search(r'\bdelivered\b', text_lower):
        delivered_dates = []
        lines = page_text.split('\n')
        for i, line in enumerate(lines):
            line_l = line.strip().lower()
            if 'estimated' in line_l or 'agreed' in line_l or 'scheduled' in line_l:
                continue
            if line_l == 'delivered':
                search_lines = lines[i:i + 3]
                for candidate in search_lines:
                    dm = re.search(r'(\d{4}/\d{2}/\d{2})', candidate)
                    if dm:
                        delivered_dates.append(dm.group(1))
                        break

        for dm in re.finditer(r'\bdelivered\s*(?:\n|\s)+(\d{4}/\d{2}/\d{2})', page_text, re.IGNORECASE):
            delivered_dates.append(dm.group(1))

        if delivered_dates:
            date_part = delivered_dates[-1]
            try:
                dt = datetime.strptime(date_part, '%Y/%m/%d')
                return {
                    'status': 'delivered',
                    'delivery_date': dt.strftime('%Y-%m-%d'),
                    'raw': f'Delivered {date_part}'
                }
            except ValueError:
                pass

        if 'your shipment is delivered' in text_lower:
            m = re.search(r'\bdelivered\s*(?:\n|\s)+(\d{4}/\d{2}/\d{2})', text_lower, re.MULTILINE)
            if m:
                date_part = m.group(1).strip()
                try:
                    dt = datetime.strptime(date_part, '%Y/%m/%d')
                    return {
                        'status': 'delivered',
                        'delivery_date': dt.strftime('%Y-%m-%d'),
                        'raw': f'Delivered {date_part}'
                    }
                except ValueError:
                    pass
            return {'status': 'delivered', 'delivery_date': None, 'raw': 'Delivered (date unclear)'}

    if 'your shipment is currently booked' in text_lower or 'currently booked' in text_lower:
        if 'cancel' in text_lower:
            return {'status': 'booked_cancelled', 'delivery_date': None, 'raw': 'Booked (cancelled)'}
        return {'status': 'booked', 'delivery_date': None, 'raw': 'Booked'}

    if (
        'your shipment is currently at dispatching center' in text_lower
        or 'currently at dispatching center' in text_lower
        or 'in transportation' in text_lower
        or 'in delivery' in text_lower
        or 'at dispatching' in text_lower
    ):
        return {'status': 'in_transport', 'delivery_date': None, 'raw': 'In transit'}

    return {'status': 'unknown', 'delivery_date': None, 'raw': page_text[:200]}


async def _check_single_stt(page, stt_number: str) -> dict:
    """Open the public myDSV tracking page and parse the visible status."""
    url = f'https://mydsv.dsv.com/app/tracking-public/?refNumber={stt_number}'

    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
    except Exception as exc:
        return {'status': 'error', 'delivery_date': None, 'raw': f'Open page failed: {exc}', 'success': False}

    # Let the Angular app render and hydrate tracking details.
    await asyncio.sleep(4)

    for selector in (
        'button:has-text("Required cookies")',
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
    ):
        try:
            btn = page.locator(selector)
            if await btn.count() > 0:
                await btn.first.click(timeout=1000)
                await asyncio.sleep(1)
                break
        except Exception:
            pass

    try:
        await page.wait_for_selector('body', timeout=10000)
    except Exception:
        pass

    # Wait specifically for the result area when possible; fall back to body.
    try:
        await page.wait_for_function(
            """() => {
                const text = document.body && document.body.innerText || '';
                return text.includes('Your shipment is delivered')
                    || text.includes('Your shipment is currently')
                    || text.includes('Shipment Details')
                    || text.includes('Shipment not found')
                    || text.includes('No data found')
                    || text.includes('captcha');
            }""",
            timeout=20000,
        )
    except Exception:
        pass

    try:
        text = await page.inner_text('body')
    except Exception:
        text = ''

    text_lower = text.lower()
    has_details = 'shipment details' in text_lower
    has_status_signal = (
        'your shipment is' in text_lower
        or re.search(r'\bdelivered\s*(?:\n|\s)+\d{4}/\d{2}/\d{2}', text, re.IGNORECASE)
        or 'currently booked' in text_lower
        or 'currently at dispatching center' in text_lower
        or 'in transportation' in text_lower
        or 'in delivery' in text_lower
    )
    if has_details and not has_status_signal:
        await asyncio.sleep(5)
        try:
            text = await page.inner_text('body')
        except Exception:
            pass

    if not text.strip():
        return {'status': 'error', 'delivery_date': None, 'raw': 'Page empty (timeout or blocked)', 'success': False}

    return classify_status(text)


def _browser_launch_candidates():
    """Return Playwright launch configs, preferring installed desktop browsers."""
    args = [
        '--disable-blink-features=AutomationControlled',
        '--no-sandbox',
        '--disable-dev-shm-usage',
    ]
    common = {
        'headless': True,
        'args': args,
    }

    candidates = []

    if sys.platform.startswith('win'):
        env_paths = [
            os.environ.get('PROGRAMFILES'),
            os.environ.get('PROGRAMFILES(X86)'),
            os.environ.get('LOCALAPPDATA'),
        ]
        browser_rel_paths = [
            os.path.join('Microsoft', 'Edge', 'Application', 'msedge.exe'),
            os.path.join('Google', 'Chrome', 'Application', 'chrome.exe'),
        ]
        for base in env_paths:
            if not base:
                continue
            for rel in browser_rel_paths:
                path = os.path.join(base, rel)
                if os.path.exists(path):
                    candidates.append(({**common, 'executable_path': path}, path))

    elif sys.platform == 'darwin':
        for path in (
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        ):
            if os.path.exists(path):
                candidates.append(({**common, 'executable_path': path}, path))

    else:
        for path in (
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/microsoft-edge',
        ):
            if os.path.exists(path):
                candidates.append(({**common, 'executable_path': path}, path))

    candidates.extend([
        ({**common, 'channel': 'msedge'}, 'Microsoft Edge channel'),
        ({**common, 'channel': 'chrome'}, 'Google Chrome channel'),
        (common, 'bundled Chromium'),
    ])
    return candidates


async def _run_verification(stt_list: list, progress_callback=None) -> list:
    """批量核实的异步主函数，串行逐条处理"""
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "缺少 Playwright 依赖，批量核实无法启动。请重新安装/打包包含 playwright 的版本。"
        ) from exc

    results = []
    browser = None
    try:
        async with async_playwright() as p:
            launch_errors = []
            for launch_kwargs, label in _browser_launch_candidates():
                try:
                    browser = await p.chromium.launch(**launch_kwargs)
                    break
                except Exception as exc:
                    launch_errors.append(f"{label}: {exc}")
            if not browser:
                raise RuntimeError(
                    "Playwright 浏览器不可用。已尝试内置 Chromium、Microsoft Edge、Chrome。"
                    "请确认办公电脑安装了 Edge/Chrome。详细错误："
                    + " | ".join(launch_errors[-3:])
                )
            context = await browser.new_context(
                locale='en-US',
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                ),
            )
            page = await context.new_page()

            for i, stt in enumerate(stt_list):
                try:
                    result = await _check_single_stt(page, stt)
                    result['stt_number'] = stt
                    result['success'] = True
                except Exception as e:
                    result = {
                        'stt_number': stt,
                        'status': 'error',
                        'delivery_date': None,
                        'raw': str(e),
                        'success': False,
                    }

                result['index'] = i + 1
                result['total'] = len(stt_list)
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, len(stt_list))

            await page.close()
            await browser.close()

    except Exception as e:
        if browser:
            try:
                await browser.close()
            except:
                pass
        processed = len(results)
        for i, stt in enumerate(stt_list[processed:], start=processed):
            results.append({
                'stt_number': stt,
                'status': 'error',
                'delivery_date': None,
                'raw': str(e),
                'success': False,
                'index': i + 1,
                'total': len(stt_list),
            })

    return results


def verify_stt_list(stt_list: list, progress_callback=None) -> list:
    """
    同步入口：批量核实 STT 列表。
    stt_list: ['PLTOU604024589', ...]
    progress_callback: 可选回调 (current_index, total)
    返回: [{'stt_number': ..., 'status': ..., 'delivery_date': ..., ...}, ...]
    """
    return asyncio.run(_run_verification(stt_list, progress_callback))
