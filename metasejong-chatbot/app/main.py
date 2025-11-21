# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Tuple
from app.rag_min import handle_chat
from app.db import ping_db
from app.orders import router as orders_router
from app.mission_events import router as mission_router

app = FastAPI(title="MetaSejong Chatbot API", version="0.1.0")
app.include_router(orders_router)
app.include_router(mission_router)


# 헬스체크
@app.get("/health")
async def health():
    db = await ping_db()
    return {"api": "ok", "db": db}


# 요청 스키마
class ChatBody(BaseModel):
    text: str
    user_xy: Optional[Tuple[float, float]] = None
    session_id: Optional[str] = "default"


# 채팅 엔드포인트
@app.post("/chat")
async def chat(body: ChatBody):
    return await handle_chat(body.text, body.user_xy)


# 루트
@app.get("/")
def root():
    return {"ok": True}
