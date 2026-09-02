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


def _application_directory() -> str:
    """
    المكان اللي فيه ملفات المستخدم: config.json و logins.csv و
    Programs و data/ و last_db*_settings.txt.

    مهم إنه يبقى جنب الـ exe نفسه، مش جوه الحزمة. في وضع onefile
    الـ bootstrap بيفك ضغط البرنامج في مكان مؤقت، ولو عملنا chdir
    هناك، كل اللي التطبيق هيكتبه هيتمسح أول ما يقفل.

    __compiled__.containing_dir هو اللي Nuitka بيرشحه، وبيدي المكان
    الصح في standalone و onefile الاتنين. مش موجود وقت التشغيل من
    السورس، فالـ NameError متوقع.
    """
    try:
        return os.path.normpath(__compiled__.containing_dir)  # type: ignore[name-defined]  # noqa: F821
    except NameError:
        pass

    if getattr(sys, "frozen", False):
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

# العنوان اللي المتصفح بيفتحه. مهم: uvicorn بيستمع على 0.0.0.0 وده
# عنوان استماع مش عنوان تصفح — لو فتحتيه في المتصفح بيدي
# ERR_ADDRESS_INVALID.
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

    الطريقة دي أضمن من مجرد sleep: التاب ما بتتفتحش غير لما الصفحة
    تبقى جاهزة، فما بتقعديش تتفرجي على صفحة بتحمّل.
    """
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
    بيفتح المتصفح *بس* لو مفيش تاب مفتوح أصلاً، وبعد ما السيرفر يجهز.

    الصفحة المفتوحة بتعمل polling على /process/status كل ثانيتين، فلو
    السيرفر شاف أي request في أول كام ثانية معناها إن فيه تاب شغال —
    والتاب ده هيلاقي الـ boot_id اتغيّر ويعمل reload لنفسه.
    وبكده إعادة التشغيل بتحدّث نفس التاب بدل ما تفتح واحد جديد كل مرة.
    """
    from fastapi_app.core import client_seen_within

    if not _wait_until_ready():
        print("[startup] server did not become ready in time - not opening a browser")
        return

    print("")
    print("=" * 60)
    print(f"  Refrigerator Vision System   ->   {BROWSE_URL}")
    print("=" * 60)
    print("")

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if client_seen_within(4.0):
            # فيه تاب مفتوح بالفعل — هيعمل reload لنفسه.
            return
        time.sleep(0.25)

    if not _open_url(BROWSE_URL):
        print(f"[browser] could not open automatically - open {BROWSE_URL} manually")


def _browser_thread():
    """أي استثناء هنا ما يوقفش السيرفر — بس لازم يتطبع مش يتبلع."""
    try:
        _open_browser_if_needed()
    except Exception as exc:  # noqa: BLE001
        print(f"[browser] helper failed: {exc!r}")
        print(f"[browser] open {BROWSE_URL} manually")


# ---------------------------------------------------------------------
# تسكيت لوج السيرفر بالكامل.
#
# uvicorn بيطبع:
#   - سطر access لكل request. الواجهة بتضرب /check-flags و
#     /check-flags2 كل ثانية و /process/status و /sql_status و
#     /station*_status كل ثانيتين، وكل فتحة صفحة معاها /static/main.js
#     و 303 و 304 … يعني الشاشة بتتملى وهي واقفة مش بتعمل حاجة.
#   - سطور بدء التشغيل: "Started server process"، "Waiting for
#     application startup"، "Uvicorn running on http://…" وهكذا.
#
# مفيش حاجة من دول بتفيد المشغّل على الخط، وكلها كانت بتدفن الرسائل
# اللي فعلًا مهمة (حالة الاتصال، بدء/إيقاف العملية، الأخطاء).
#
#   access_log=False   → مفيش أي سطر request خالص
#   log_level="error"  → مفيش سطور بدء/إيقاف، بس لو حصل خطأ حقيقي
#
# الترمينال دلوقتي بيعرض رسايل البرنامج نفسه بس.
# (لو احتجت تدبّج مشكلة: غيّر log_level لـ "info" و access_log لـ True.)
# ---------------------------------------------------------------------

if __name__ == "__main__":
    threading.Thread(target=_browser_thread, daemon=True).start()

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="error",
        access_log=False,
    )
