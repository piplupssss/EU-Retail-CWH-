"""
DB Schenker 累积发票 PDF 解析模块
从 PDF 中提取：发票号、日期、总净额、每条运单的 STT 号 + 净额 + Ref 日期
"""
import re


def parse_polish_amount(text):
    """将波兰格式数字转换为浮点数
    例: '1,094.50' → 1094.50, '24,559.93' → 24559.93, '1,014,24' → 1014.24
    波兰格式：小数点做千分位分隔符，逗号做小数分隔符
    但实际发票中也有 '1,094.50' 这种混合格式
    """
    if not text:
        return 0.0
    text = text.strip().replace(' ', '')
    # 去掉 PLN 前缀
    text = text.replace('PLN', '').strip()
    # 处理波兰格式：1.094,50 → 1094.50 或 1,014,24 → 1014.24
    # 也处理混合格式：1,094.50 → 1094.50
    if ',' in text and '.' in text:
        # 1,094.50 → 千分位用逗号，小数用点 → 去掉逗号
        text = text.replace(',', '')
    elif ',' in text:
        # 只有一个逗号，可能是小数分隔符：1,50 → 1.50 或 24,559 → 24559
        # 也可能是千分位：1,014,24 → 这种需要去掉逗号
        parts = text.split(',')
        if len(parts) > 2:
            # 1,014,24 → 千分位 + 小数 → 去掉所有逗号变 101424，然后插入小数点
            text = text.replace(',', '')[:-2] + '.' + text.replace(',', '')[-2:]
        else:
            # 1,50 或 24,559 → 判断是千分位还是小数
            last_part = parts[-1]
            if len(last_part) == 2:
                # 1,50 → 1.50 (小数)
                text = parts[0] + '.' + last_part
            else:
                # 24,559 → 24559 (千分位，无小数)
                text = text.replace(',', '')
    try:
        return float(text)
    except ValueError:
        return 0.0


def parse_invoice_pdf(pdf_path):
    """解析 DB Schenker 累积发票 PDF，返回结构化数据"""
    import pdfplumber

    invoice_number = None
    invoice_date = None
    total_net = 0.0
    currency = 'PLN'
    items = []

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ''
        for page in pdf.pages:
            text = page.extract_text() or ''
            full_text += text + '\n'

        # 提取发票号
        m = re.search(r'Faktura zbiorcza:\s*(\d+)', full_text)
        if m:
            invoice_number = m.group(1)

        # 提取发票日期
        date_match = re.search(r'Łódź,\s*(\d{4}-\d{2}-\d{2})', full_text)
        if date_match:
            invoice_date = date_match.group(1)

        # 提取总净额
        m = re.search(r'Wartość netto:\s*PLN\s*([\d\s,.]+)', full_text)
        if m:
            total_net = parse_polish_amount(m.group(1))

        # 提取每条运单信息
        # 用 "Numer T&T:" 分割每条运单，这样更可靠
        # 每条运单块从 Numer T&T 开始到下一条或 Wartość netto PLN 结束
        stt_blocks = re.split(r'(?=Numer T&T:\s*\S+)', full_text)

        for block in stt_blocks:
            stt_match = re.search(r'Numer T&T:\s*(\S+)', block)
            if not stt_match:
                continue
            stt_number = stt_match.group(1)

            # 提取净额 - 在当前运单块中找最后出现的 Wartość netto PLN
            net_matches = re.findall(r'Wartość netto\s+PLN\s*([\d\s,.]+)', block)
            net_amount = parse_polish_amount(net_matches[-1]) if net_matches else 0.0

            # 提取 Ref 中的日期尖括号内容
            # 格式: Ref.: <PL Jan 15><RHQ Retail><Premium>PRO
            ref_match = re.search(r'Ref[^<]*<([^>]+)>', block)
            ref_date = ''
            if ref_match:
                ref_date = ref_match.group(1).strip()

            items.append({
                'stt_number': stt_number,
                'net_amount': net_amount,
                'ref_date': ref_date,
            })

    return {
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
        'total_net': total_net,
        'currency': currency,
        'items': items
    }