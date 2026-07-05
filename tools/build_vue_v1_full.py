from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "eu-retail-cwh-system"
BASE_FULL = ROOT / "github_publish" / "full-packages" / "EUCWH-VN62-Full-Clean-20260705-2155.zip"
STAMP = datetime.now().strftime("%Y%m%d-%H%M")
VERSION = "V1"
PACKAGE_NAME = f"EU-Retail-CWH-System-{VERSION}-{STAMP}"
BUILD_ROOT = Path("/private/tmp") / PACKAGE_NAME
OUT_DIR = ROOT / "github_publish" / "full-packages"
OUT_ZIP = OUT_DIR / f"{PACKAGE_NAME}.zip"


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path, ignore=None) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=ignore)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zip_dir(src_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src_dir.rglob("*")):
            if path.is_dir():
                zf.write(path, path.relative_to(src_dir.parent).as_posix() + "/")
            elif path.is_file():
                zf.write(path, path.relative_to(src_dir.parent).as_posix())


def compile_launcher(build_dir: Path) -> None:
    icon_src = SRC / "frontend" / "src" / "assets" / "cwh_logo.jpg"
    icon = build_dir / "cwh_logo.ico"
    try:
        from PIL import Image

        Image.open(icon_src).convert("RGBA").save(
            icon,
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
    except Exception:
        icon = ROOT / "vn8" / "app" / "static" / "cwh_logo.ico"

    source = build_dir / "launcher_eu_retail_cwh.c"
    source.write_text(
        r'''
#include <windows.h>
#include <shellapi.h>
#include <wchar.h>

static void dirname_inplace(wchar_t *path) {
    wchar_t *p = wcsrchr(path, L'\\');
    if (p) *p = 0;
}

int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE hPrev, LPWSTR cmdLine, int show) {
    wchar_t exe[MAX_PATH];
    GetModuleFileNameW(NULL, exe, MAX_PATH);
    dirname_inplace(exe);

    wchar_t python[MAX_PATH], runpy[MAX_PATH];
    swprintf(python, MAX_PATH, L"%ls\\_system\\python\\pythonw.exe", exe);
    swprintf(runpy, MAX_PATH, L"\"%ls\\_system\\run.py\"", exe);

    SetEnvironmentVariableW(L"AUTO_OPEN_BROWSER", L"1");
    HINSTANCE res = ShellExecuteW(NULL, L"open", python, runpy, exe, SW_HIDE);
    if ((INT_PTR)res <= 32) {
        MessageBoxW(NULL, L"Unable to start EU Retail CWH System. Please use _tools\\debug_start.bat.", L"EU Retail CWH System", MB_ICONERROR);
        return 1;
    }
    return 0;
}
''',
        encoding="utf-8",
    )
    rc = source.with_suffix(".rc")
    res = source.with_suffix(".res")
    rc.write_text(f'IDI_ICON1 ICON "{icon.as_posix()}"\n', encoding="utf-8")
    subprocess.run(["x86_64-w64-mingw32-windres", str(rc), "-O", "coff", "-o", str(res)], check=True)
    subprocess.run(
        [
            "x86_64-w64-mingw32-gcc",
            "-municode",
            "-mwindows",
            "-O2",
            str(source),
            str(res),
            "-o",
            str(build_dir / "EU Retail CWH System.exe"),
            "-lshell32",
        ],
        check=True,
    )
    for artifact in [source, rc, res]:
        artifact.unlink(missing_ok=True)


def main() -> None:
    subprocess.run(["npm", "run", "build"], cwd=SRC / "frontend", check=True)

    if BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)
    BUILD_ROOT.mkdir(parents=True)

    with zipfile.ZipFile(BASE_FULL) as zf:
        zf.extractall(BUILD_ROOT.parent)

    extracted = BUILD_ROOT.parent / "EUCWH-VN62-Full-Clean-20260705-2155"
    if extracted.exists():
        extracted.rename(BUILD_ROOT)

    system = BUILD_ROOT / "_system"
    app_dst = system / "app"
    app_src = SRC / "backend" / "app"
    keep_python = system / "python"
    if not keep_python.exists():
        raise RuntimeError("Base package does not contain embedded Python")

    if app_dst.exists():
        shutil.rmtree(app_dst)
    ignore = shutil.ignore_patterns(
        "data",
        "__pycache__",
        "*.pyc",
        "warehouse.db",
        "wms.db",
        "wms.db-*",
        "static/images/*",
    )
    copy_tree(app_src, app_dst, ignore=ignore)
    shutil.rmtree(app_dst / "static" / "images", ignore_errors=True)
    (app_dst / "data" / "uploads").mkdir(parents=True, exist_ok=True)
    (app_dst / "data" / "backups").mkdir(parents=True, exist_ok=True)
    (app_dst / "static" / "images").mkdir(parents=True, exist_ok=True)
    copy_file(SRC / "backend" / "run.py", system / "run.py")
    copy_file(SRC / "backend" / "requirements.txt", system / "requirements.txt")

    for old_name in ["EUCWH-VN62.exe", "EUCWH-VN61.exe", "EUCWH-VN60.exe"]:
        old = BUILD_ROOT / old_name
        if old.exists():
            old.unlink()
    compile_launcher(BUILD_ROOT)

    tools = BUILD_ROOT / "_tools"
    shutil.rmtree(tools, ignore_errors=True)
    tools.mkdir(exist_ok=True)
    write_text(
        BUILD_ROOT / "stop_system.bat",
        """@echo off
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001') do taskkill /PID %%a /F >nul 2>nul
""",
    )
    write_text(
        tools / "debug_start.bat",
        """@echo off
cd /d %~dp0\\..
set AUTO_OPEN_BROWSER=1
_system\\python\\python.exe _system\\run.py
pause
""",
    )
    write_text(
        BUILD_ROOT / "README.txt",
        f"""EU Retail CWH System {VERSION}

启动：
  双击 EU Retail CWH System.exe

停止：
  双击 stop_system.bat

数据恢复：
  进入数据管理中心，上传你备份的 core_backup_no_images.xlsx 和 images 文件夹。

说明：
  本完整包不包含业务数据、物流源文件、发票源文件、数据库和历史备份。
  数据只在本机处理；系统更新仅下载程序包。
""",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_dir(BUILD_ROOT, OUT_ZIP)
    digest = sha256(OUT_ZIP)
    (OUT_ZIP.with_suffix(OUT_ZIP.suffix + ".sha256")).write_text(
        f"{digest}  {OUT_ZIP.name}\n", encoding="utf-8"
    )
    print(OUT_ZIP)
    print(digest)


if __name__ == "__main__":
    main()
