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


# ---------------------------------------------------------------------
# لازم يتنفذ *قبل* أي import بيطبع حاجة.
#
# على ويندوز الـ console بيبقى cp1252، وأي print فيه إيموجي أو عربي
# بيرمي UnicodeEncodeError. ده مش تحذير — ده بيقتل الـ startup:
# realtime.start_tickers كان بيقع في lifespan والسيرفر بيخرج بـ code 3.
#
# errors="replace" هو المهم: أي حرف مش متدعوم بيتحوّل لـ '?' بدل ما
# يرمي exception. يعني حتى لو حد ضاف إيموجي جديد في print بعدين،
# التطبيق مش هيقع.
# ---------------------------------------------------------------------
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _is_frozen() -> bool:
    """
    هل إحنا شغالين من ملف تنفيذي مبني؟

    PyInstaller بيحط sys.frozen، لكن Nuitka *مبيحطهاش* — بيحط
    __compiled__ في كل موديول متكمبايل. لازم نتحقق من الاتنين، وإلا
    مسار المشروع بيتحسب غلط ويدوّر على config.json في المكان الخطأ.
    """
    return getattr(sys, "frozen", False) or "__compiled__" in globals()


def _application_directory() -> str:
    if _is_frozen():
        return os.path.normpath(os.path.dirname(sys.executable))
    return os.path.normpath(os.path.dirname(os.path.abspath(__file__)))


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

def _open_browser_if_needed(wait_seconds: float = 4.0):
    """
    بيفتح المتصفح *بس* لو مفيش تاب مفتوح أصلاً.

    الصفحة المفتوحة بتعمل polling على /process/status كل ثانيتين، فلو
    السيرفر شاف أي request في أول كام ثانية معناها إن فيه تاب شغال —
    والتاب ده هيلاقي الـ boot_id اتغيّر ويعمل reload لنفسه.
    وبكده إعادة التشغيل بتحدّث نفس التاب بدل ما تفتح واحد جديد كل مرة.
    """
    from fastapi_app.core import client_seen_within

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if client_seen_within(wait_seconds):
            print(" Existing browser tab detected — refreshing it instead of opening a new one")
            return
        time.sleep(0.25)

    webbrowser.open(f"http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    threading.Thread(target=_open_browser_if_needed, daemon=True).start()

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
