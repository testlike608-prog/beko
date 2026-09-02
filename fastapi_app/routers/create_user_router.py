"""Create user page — FastAPI version of the `CreateUser` blueprint."""

from __future__ import annotations

import csv
import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from ..core import templates

router = APIRouter(tags=["create_user"])

LOGINS_FILE = "logins.csv"

<<<<<<< HEAD

@router.get("/create_user", response_class=HTMLResponse, name="CreateUser.create_user")
async def create_user_page(request: Request):
    if request.session.get("auth") != "admin":
=======
# مين اللي مسموح له يفتح صفحة إنشاء المستخدمين
ALLOWED_ROLES = ("admin", "dev")


@router.get("/create_user", response_class=HTMLResponse, name="CreateUser.create_user")
async def create_user_page(request: Request):
    auth_role = request.session.get("auth")
    if auth_role not in ALLOWED_ROLES:
>>>>>>> 9bf21a6 (ADD debug mode)
        return PlainTextResponse("Access denied", status_code=403)

    return templates.TemplateResponse(
        request,
        "CREATE_USER_HTML.html",
        {
            "error": "",
<<<<<<< HEAD
=======
            "auth": auth_role,
>>>>>>> 9bf21a6 (ADD debug mode)
            "NewUser_data": {"username": "", "password": "", "auth": ""},
        },
    )


@router.post("/create_user", response_class=HTMLResponse, name="CreateUser.create_user_post")
async def create_user_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    Authentication: str = Form(""),
):
<<<<<<< HEAD
    if request.session.get("auth") != "admin":
=======
    auth_role = request.session.get("auth")
    if auth_role not in ALLOWED_ROLES:
>>>>>>> 9bf21a6 (ADD debug mode)
        return PlainTextResponse("Access denied", status_code=403)

    username = (username or "").strip()
    password = (password or "").strip()
    auth = (Authentication or "").strip()
    new_user_data = {"username": username, "password": password, "auth": auth}

    if not username or not password or not auth:
        return templates.TemplateResponse(
            request,
            "CREATE_USER_HTML.html",
            {
<<<<<<< HEAD
                "error": "Please fill all fields",
=======
                "error": "⚠️ Please fill all fields",
                "auth": auth_role,
                "NewUser_data": new_user_data,
            },
        )

    # الأدوار المسموح بيها (admin و dev الاتنين يقدروا يعملوا مستخدم dev،
    # عشان يكون فيه طريقة تدخل بيها على تاب المطوّر لأول مرة)
    if auth not in ("admin", "user", "dev"):
        return templates.TemplateResponse(
            request,
            "CREATE_USER_HTML.html",
            {
                "error": "⚠️ You are not allowed to assign this role",
                "auth": auth_role,
>>>>>>> 9bf21a6 (ADD debug mode)
                "NewUser_data": new_user_data,
            },
        )

    with open(LOGINS_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                username,
                password,
                auth,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    return templates.TemplateResponse(
        request,
        "CREATE_USER_HTML.html",
        {
<<<<<<< HEAD
            "message": "User created  successfully!",
=======
            "message": "✅ User created  successfully!",
            "auth": auth_role,
>>>>>>> 9bf21a6 (ADD debug mode)
            "NewUser_data": new_user_data,
        },
    )
