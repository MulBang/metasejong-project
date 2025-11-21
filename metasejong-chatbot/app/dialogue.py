# app/dialogue.py
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
import time


class Phase(str, Enum):
    RECOMMEND = "RECOMMEND"  # 의도 이해 + 후보 제시
    ASK_PICKUP = "ASK_PICKUP"  # 수령(드롭오프) 건물 선택 유도
    CONFIRM_ORDER = "CONFIRM_ORDER"  # 최종 확인(메뉴 확정 + 가격 표시)
    DISPATCH = "DISPATCH"  # mission 생성/호출


# 간단 메모리(프로토타입) — 실서비스면 Redis/DB 권장
SESSION: Dict[str, Dict[str, Any]] = {}


def get_session(sid: str) -> Dict[str, Any]:
    st = SESSION.setdefault(
        sid,
        {
            "phase": Phase.RECOMMEND,
            "last_seen": time.time(),
            "intent": None,  # "recommend" 등
            "keywords": [],  # 의미 확장된 키워드
            "menu_choice": None,  # {menu_id, name, price, restaurant, building}
            "pickup_poi_id": None,  # 선택된 수령 POI
            "pickup_building_id": None,
            "pickup_building_name": None,
            "drop_candidates": [],  # 드롭오프 건물 후보 목록
            "user_xy": None,  # (x, y)
        },
    )
    st["last_seen"] = time.time()
    return st
