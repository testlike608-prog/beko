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
        "running": bool(status.get("running")),
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

    result = controller.set_debug_mode(enabled, dry_run=dry_run)
    result.update(_state())
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


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

    result = controller.simulate_trigger(
        station,
        result=str(payload.get("result") or "PASS"),
        dummy=str(payload.get("dummy") or ""),
        sku=str(payload.get("sku") or ""),
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

    return JSONResponse({"ok": True, "message": f"{kind} S{station} = {value}", **_state()})


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

    result = controller.write_output(function_name, action)
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


@router.post("/io/off_all", name="debug.io_off_all")
def debug_io_off_all(request: Request):
    denied = _guard(request)
    if denied is not None:
        return denied

    app = controller.app
    if app is None:
        return JSONResponse(
            {"ok": True, "sent": False, "message": "No hardware connection — nothing sent"}
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
    cc.Manual_Scanner_MODE = False
    cc.Manual_Scanner_MODE2 = False

    return JSONResponse({"ok": True, "message": "Display flags reset", **_state()})
