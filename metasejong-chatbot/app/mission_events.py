# app/mission_events.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from app.db_mission import format_mission_event_message, get_mission_context, get_engine

router = APIRouter(prefix="/mission", tags=["mission"])


class MissionEventIn(BaseModel):
    mission_id: int
    type: str  # "ARRIVE_PICKUP" | "ARRIVE_DROPOFF" | "DONE" 등
    note: Optional[str] = None


@router.post("/events")
async def post_mission_event(ev: MissionEventIn):
    ev_type = ev.type.upper().strip()
    # DB ENUM과 맞추기 위한 정규화
    norm = {
        "ARRIVE_PICKUP": "ARRIVED_PICKUP",
        "ARRIVE_DROPOFF": "ARRIVED_DROPOFF",
        "DROPOFF_DONE": "DONE",
    }
    ev_type = norm.get(ev_type, ev_type)

    # 1) 미션 존재 확인
    ctx = get_mission_context(ev.mission_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="mission not found")

    # 2) 이벤트 기록 + 상태 갱신(아주 얇게)
    eng = get_engine()
    with eng.begin() as conn:
        # DB는 timestamp 컬럼명이 ts 임
        conn.execute(
            text(
                "INSERT INTO mission_events (mission_id, phase, ts, note) VALUES (:mid,:ph,NOW(),:nt)"
            ),
            {"mid": ev.mission_id, "ph": ev_type, "nt": ev.note or ""},
        )
        new_status = None
        # DB ENUM: queued/running/done/failed
        if ev_type == "ARRIVED_PICKUP":
            new_status = "running"
        elif ev_type == "ARRIVED_DROPOFF":
            new_status = "running"
        elif ev_type in ("DONE",):
            new_status = "done"
        if new_status:
            conn.execute(
                text("UPDATE missions SET status=:st WHERE id=:mid"),
                {"st": new_status, "mid": ev.mission_id},
            )

    # 3) 사용자에게 보여줄 문구 생성
    #    - ARRIVE_PICKUP: “[건물] 도착!... 이제 [사용자건물]으로…”
    #    - DONE: “음식 배송 완료했습니다! …”
    user_msg = format_mission_event_message(ev_type, ev.mission_id)
    if not user_msg:
        # 지원하지 않는 타입이면 기본 포맷 (필요시 템플릿을 더 추가해도 됨)
        user_msg = f"이벤트({ev_type})가 접수되었습니다."

    return {
        "ok": True,
        "mission_id": ev.mission_id,
        "event_type": ev_type,
        "message_for_user": user_msg,
    }
