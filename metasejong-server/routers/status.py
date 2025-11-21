from fastapi import APIRouter
from db.session import quick_health


router = APIRouter()


@router.get("/status")
async def status():
    return {"status": "ok", **quick_health()}
