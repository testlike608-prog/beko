"""
Developer / Debug endpoints
---------------------------
الراوتس دي كلها للمطوّر بس (auth == 'dev') وبتخدم تاب "Developer"
في الداشبورد:

    GET  /debug/status        -> حالة وضع الديباج
    POST /debug/mode          -> تشغيل/إطفاء وضع الديباج (مش محتاج START)
    POST /debug/trigger       -> محاكاة "وصلت تلاجة" على محطة 1 أو 2
    POST /debug/alert         -> رفع/تنزيل فلاج أليرت (NO CSV / Manual scanner)
    POST /debug/io            -> إرسال أمر ON/OFF لمخرج واحد
    POST /debug/io/off_all    -> إطفاء كل المخارج
    POST /debug/reset_flags   -> تصفير فلاجات العرض (arrived / result / dummy)
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import ClientsClass as cc
import ioSetting
from process_control import controller

router = APIRouter(prefix="/debug", tags=["debug"])

# المخارج اللي ينفع تتحكمي فيها يدويًا من التاب
OUTPUT_FUNCTIONS = (
    "LIGHTING_S1", "LIGHTING_S2",
    "SCANNER_S1", "SCANNER_S2",
    "BUZZER_S1", "BUZZER_S2",
    "TESTDONE_S1", "TESTDONE_S2",
    "FAILURE",
)


def _guard(request: Request):
    """المطوّر بس."""
    if not request.session.get("username"):
        return JSONResponse({"ok": False, "message": "Not authenticated"}, status_code=401)
    if request.session.get("auth") != "dev":
        return JSONResponse({"ok": False, "message": "Developer access required"}, status_code=403)
    return None


def _state() -> dict:
    status = controller.status()
    return {
        "ok": True,
        "debug": bool(status.get("debug")),
        "dry_run": bool(status.get("dry_run")),
        "listen_io": bool(status.get("listen_io")),
        "running": bool(status.get("running")),
        "station_busy": {
            "1": bool(controller.app.is_station_busy(1)) if controller.app else False,
            "2": bool(controller.app.is_station_busy(2)) if controller.app else False,
        },
        "state": status.get("state"),
        "outputs": [name for name in OUTPUT_FUNCTIONS if name in ioSetting.io_mapping],
        "flags": {
            "no_csv_s1": cc.NO_CSV_ERROR,
            "no_csv_s2": cc.NO_CSV_ERROR2,
            "manual_scanner_s1": cc.Manual_Scanner_MODE,
            "manual_scanner_s2": cc.Manual_Scanner_MODE2,
        },
        "status": status,
    }


@router.get("/status", name="debug.status")
def debug_status(request: Request):
    denied = _guard(request)
    if denied is not None:
        return denied
    return JSONResponse(_state())


@router.post("/mode", name="debug.mode")
async def debug_mode(request: Request):
    denied = _guard(request)
    if denied is not None:
        return denied

    payload = await request.json()
    enabled = bool(payload.get("enabled"))
    dry_run = bool(payload.get("dry_run"))
    # لو الواجهة ما بعتتش القيمة، الافتراضي إننا نسمع للـ I/O كمان
    listen_io = bool(payload.get("listen_io", True))

    result = await asyncio.to_thread(
        controller.set_debug_mode, enabled, dry_run, listen_io)

    # الترتيب مهم: _state() الأول عشان result يفضل هو صاحب الكلمة
    # الأخيرة في ok/message — العكس كان بيخفي أي فشل.
    body = {**_state(), **result}
    return JSONResponse(body, status_code=200 if body.get("ok") else 409)


@router.post("/trigger", name="debug.trigger")
async def debug_trigger(request: Request):
    denied = _guard(request)
    if denied is not None:
        return denied

    payload = await request.json()
    try:
        station = int(payload.get("station", 0))
    except (TypeError, ValueError):
        station = 0

    result = await asyncio.to_thread(
        controller.simulate_trigger,
        station,
        str(payload.get("result") or "PASS"),
        str(payload.get("dummy") or ""),
        str(payload.get("sku") or ""),
    )
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


@router.post("/alert", name="debug.alert")
async def debug_alert(request: Request):
    """رفع أو تنزيل فلاج أليرت يدويًا — لتجربة جرس الأليرتس."""
    denied = _guard(request)
    if denied is not None:
        return denied

    payload = await request.json()
    kind = str(payload.get("kind") or "no_csv").lower()
    station = 2 if str(payload.get("station")) == "2" else 1
    value = bool(payload.get("value", True))

    if kind == "no_csv":
        if station == 1:
            cc.NO_CSV_ERROR = value
        else:
            cc.NO_CSV_ERROR2 = value
    elif kind == "manual_scanner":
        if station == 1:
            cc.Manual_Scanner_MODE = value
        else:
            cc.Manual_Scanner_MODE2 = value
    else:
        return JSONResponse({"ok": False, "message": f"Unknown alert kind: {kind}"}, status_code=400)

    return JSONResponse({**_state(), "ok": True, "message": f"{kind} S{station} = {value}"})


@router.post("/io", name="debug.io")
async def debug_io(request: Request):
    denied = _guard(request)
    if denied is not None:
        return denied

    payload = await request.json()
    function_name = str(payload.get("function") or "")
    action = str(payload.get("action") or "").upper()

    if function_name not in OUTPUT_FUNCTIONS:
        return JSONResponse({"ok": False, "message": "Unknown output"}, status_code=400)
    if action not in ("ON", "OFF"):
        return JSONResponse({"ok": False, "message": "action must be ON or OFF"}, status_code=400)

    result = await asyncio.to_thread(controller.write_output, function_name, action)
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


@router.post("/io/off_all", name="debug.io_off_all")
def debug_io_off_all(request: Request):
    denied = _guard(request)
    if denied is not None:
        return denied

    if controller.is_dry_run():
        return JSONResponse(
            {"ok": False, "sent": False,
             "message": "Dry-run has no connection to the I/O - switch to Debug mode"},
            status_code=409,
        )

    app = controller.app
    if app is None:
        return JSONResponse(
            {"ok": False, "sent": False,
             "message": "Process is not running - start Debug mode first"},
            status_code=409,
        )

    try:
        app.client_write_io.send_request(cc.CMD_OFF_ALL, is_hex=True)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "message": f"Failed to send: {exc}"}, status_code=409)

    return JSONResponse({"ok": True, "sent": True, "message": "All outputs OFF"})


@router.post("/reset_flags", name="debug.reset_flags")
def debug_reset_flags(request: Request):
    denied = _guard(request)
    if denied is not None:
        return denied

    cc.your_s1_arrived_flag = False
    cc.your_s2_arrived_flag = False
    cc.your_s1_result = None
    cc.your_s2_result = None
    cc.your_s1_dummy = ""
    cc.your_s2_dummy = ""
    cc.your_s1_sku = ""
    cc.your_s2_sku = ""
    cc.NO_CSV_ERROR = False
    cc.NO_CSV_ERROR2 = False
    cc.NO_CSV_FILE = ""
    cc.NO_CSV_FILE2 = ""
    cc.Manual_Scanner_MODE = False
    cc.Manual_Scanner_MODE2 = False

    return JSONResponse({**_state(), "ok": True, "message": "Display flags reset"})
