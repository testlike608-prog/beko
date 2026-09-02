"""
main_fastapi.py
---------------
نقطة التشغيل لنسخة FastAPI.

    python main_fastapi.py

العملية (Start_connetion + ثريدات القراءة والمعالجة) مش بتشتغل تلقائيًا —
لازم تضغط زرار START من الصفحة الرئيسية.

النسخة القديمة (Flask) لسه موجودة في main.py من غير أي تعديل.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser

import uvicorn


def _application_directory() -> str:
    if getattr(sys, "frozen", False):
        return os.path.normpath(os.path.dirname(sys.executable))
    return os.path.normpath(os.path.dirname(os.path.abspath(__file__)))


# الكونسول بتاع ويندوز أحيانًا بيبقى cp1252، وأي رمز بره النطاق ده
# بيرمي UnicodeEncodeError جوه الثريد ويوقّفه من غير ما حد ياخد باله.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


APP_ROOT = _application_directory()

HOST = "0.0.0.0"
PORT = 5000

# مهم جدًا: نغيّر الـ cwd ونضيف مسار المشروع *قبل* أي import،
# لأن موديولات كتير (helpers, ioSetting, auth) بتقرا/تكتب ملفات بمسارات نسبية
# وقت الاستيراد نفسه (logins.csv, Station1.csv, config.json ...).
os.chdir(APP_ROOT)
sys.path.insert(0, APP_ROOT)

if not os.path.exists("data"):
    os.makedirs("data")

from fastapi_app.app import app  # noqa: E402

# العنوان اللي المتصفح بيفتحه. مهم: uvicorn بيطبع 0.0.0.0 وده عنوان
# استماع مش عنوان تصفح — لو فتحتيه في المتصفح بيدي ERR_ADDRESS_INVALID.
BROWSE_URL = f"http://127.0.0.1:{PORT}"


def _open_url(url: str) -> bool:
    """يفتح اللينك بأي طريقة متاحة. بيرجع True لو نجح."""
    try:
        if webbrowser.open(url):
            return True
    except Exception as exc:  # noqa: BLE001
        print(f"[browser] webbrowser.open failed: {exc}")

    # على ويندوز الـ default browser مش دايمًا بيتسجّل في webbrowser،
    # فبنجرّب الطريقة بتاعة النظام نفسه.
    try:
        if os.name == "nt":
            os.startfile(url)  # type: ignore[attr-defined]
            return True
    except Exception as exc:  # noqa: BLE001
        print(f"[browser] os.startfile failed: {exc}")

    try:
        import subprocess

        subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[browser] start command failed: {exc}")

    return False


def _wait_until_ready(timeout: float = 60.0) -> bool:
    """
    بيفضل يسأل /healthz لحد ما السيرفر يرد فعلًا.

    الطريقة دي أضمن من مجرد sleep: التاب ما بيتفتحش غير لما الصفحة
    تبقى جاهزة، فما بتقعديش تتفرجي على صفحة بتحمّل.
    """
    import urllib.error
    import urllib.request

    url = f"{BROWSE_URL}/healthz"
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.3)

    return False


def _open_browser_if_needed(wait_seconds: float = 4.0):
    """
    بيفتح المتصفح *بس* لو مفيش تاب مفتوح أصلاً.

    الصفحة المفتوحة بتعمل polling على /process/status كل ثانيتين، فلو
    السيرفر شاف أي request في أول كام ثانية معناها إن فيه تاب شغال —
    والتاب ده هيلاقي الـ boot_id اتغيّر ويعمل reload لنفسه.
    وبكده إعادة التشغيل بتحدّث نفس التاب بدل ما تفتح واحد جديد كل مرة.
    """
    from fastapi_app.core import client_seen_within

    print("[startup] waiting for the server to be ready ...")
    if not _wait_until_ready():
        print("[startup] server did not become ready in time - not opening a browser")
        return

    print("")
    print("=" * 60)
    print(f"  Refrigerator Vision System   ->   {BROWSE_URL}")
    print("=" * 60)
    print("")

    # السيرفر جاهز دلوقتي: نستنى شوية نشوف لو فيه تاب مفتوح أصلاً بيكلّمه.
    # لو فيه، هو هيلاقي الـ boot_id اتغيّر ويعمل reload لنفسه، فما نفتحش تاب جديد.
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if client_seen_within(4.0):
            print("[browser] existing tab detected - it will refresh itself")
            return
        time.sleep(0.25)

    print(f"[browser] opening {BROWSE_URL} ...")
    if not _open_url(BROWSE_URL):
        print(f"[browser] could not open automatically - open {BROWSE_URL} manually")


def _browser_thread():
    """أي استثناء هنا ما يوقفش السيرفر — بس لازم يتطبع مش يتبلع."""
    try:
        _open_browser_if_needed()
    except Exception as exc:  # noqa: BLE001
        print(f"[browser] helper failed: {exc!r}")
        print(f"[browser] open {BROWSE_URL} manually")


if __name__ == "__main__":
    threading.Thread(target=_browser_thread, daemon=True).start()

    # هادي عن قصد: من غير سطور INFO ولا access log — الوارنينج
    # والإيرور بس هي اللي بتظهر.
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", access_log=False)