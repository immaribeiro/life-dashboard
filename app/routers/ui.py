from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/history")
async def history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@router.get("/reminders")
async def reminders_page(request: Request):
    return templates.TemplateResponse("reminders.html", {"request": request})

@router.get("/settings")
async def settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})
