# app/db_mission.py
import asyncio
import os
from typing import Optional, Tuple, Dict

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
_engine = create_engine(os.getenv("DB_URL"), pool_pre_ping=True, future=True)


def get_engine():
    return _engine


# ─────────────────────────────────────────────
# 내부 유틸: POI 선택(우선순위 + 최근접)
# ─────────────────────────────────────────────


def _pick_poi_with_priority(
    conn, building_id: int, user_xy: Optional[Tuple[float, float]], role: str
) -> Optional[int]:
    """
    role: 'pickup' | 'dropoff'
    pickup 우선순위: entrance(0) > counter/pickup(1) > 기타(9)
    dropoff 우선순위: entrance(0) > 기타(9)
    동일 우선순위에서는 user_xy 최근접(없으면 id ASC)
    """
    if role == "pickup":
        pri_sql = """
            CASE
              WHEN LOWER(p.label) LIKE '%entrance%' OR p.label LIKE '%입구%' THEN 0
              WHEN LOWER(p.label) LIKE '%counter%' OR LOWER(p.label) LIKE '%pickup%' OR p.label LIKE '%픽업%' THEN 1
              ELSE 9
            END
        """
    else:
        pri_sql = """
            CASE
              WHEN LOWER(p.label) LIKE '%entrance%' OR p.label LIKE '%입구%' THEN 0
              ELSE 9
            END
        """

    if user_xy:
        ux, uy = user_xy
        q = text(
            f"""
            SELECT p.id
            FROM pois p
            WHERE p.building_id = :bid
            ORDER BY ({pri_sql}) ASC,
                     POW(p.x - :ux, 2) + POW(p.y - :uy, 2) ASC,
                     p.id ASC
            LIMIT 1
            """
        )
        row = conn.execute(q, {"bid": building_id, "ux": ux, "uy": uy}).first()
    else:
        q = text(
            f"""
            SELECT p.id
            FROM pois p
            WHERE p.building_id = :bid
            ORDER BY ({pri_sql}) ASC, p.id ASC
            LIMIT 1
            """
        )
        row = conn.execute(q, {"bid": building_id}).first()
    return row[0] if row else None


def _resolve_pickup_poi(
    conn, restaurant_id: int, user_xy: Optional[Tuple[float, float]]
) -> Optional[int]:
    rb = conn.execute(
        text("SELECT building_id FROM restaurants WHERE id=:rid"),
        {"rid": restaurant_id},
    ).first()
    if not rb:
        return None
    return _pick_poi_with_priority(conn, rb[0], user_xy, role="pickup")


def _resolve_dropoff_poi(
    conn, dropoff_building_id: int, user_xy: Optional[Tuple[float, float]]
) -> Optional[int]:
    return _pick_poi_with_priority(conn, dropoff_building_id, user_xy, role="dropoff")


# ─────────────────────────────────────────────
# 미션 생성
# ─────────────────────────────────────────────


async def create_mission_from_selection(
    user_msg: str,
    menu_id: Optional[int],
    restaurant_id: Optional[int],
    pickup_poi_id: Optional[int],
    dropoff_poi_id: Optional[int],
    dropoff_building_id: Optional[int] = None,
    user_xy: Optional[Tuple[float, float]] = None,
):
    """
    비어있는 필드를 최대한 자동 보완하여 missions / (mission_points) / mission_events 생성.
    - menu_id → restaurant_id 역추적
    - restaurant_id → pickup_poi 자동
    - dropoff_building_id → dropoff_poi 자동(없으면 dropoff_poi_id 그대로 사용)
    """

    def _tx():
        with _engine.begin() as conn:
            nonlocal restaurant_id, pickup_poi_id, dropoff_poi_id, menu_id

            # 1) menu_id → restaurant_id 역추적
            if menu_id and not restaurant_id:
                r = conn.execute(
                    text("SELECT restaurant_id FROM menus WHERE id=:mid"),
                    {"mid": menu_id},
                ).first()
                if r:
                    restaurant_id = r[0]

            # 2) pickup poi 자동
            if not pickup_poi_id and restaurant_id:
                pickup_poi_id = _resolve_pickup_poi(conn, restaurant_id, user_xy)

            # 3) dropoff poi 자동
            if not dropoff_poi_id and dropoff_building_id:
                dropoff_poi_id = _resolve_dropoff_poi(
                    conn, dropoff_building_id, user_xy
                )

            if not pickup_poi_id or not dropoff_poi_id:
                return {
                    "ok": False,
                    "error": "pickup_poi_id/dropoff_poi_id could not be resolved.",
                }

            # 4) 표시용 컨텍스트 조회 (menu_id 유무에 따라 분기)
            ctx = None
            if menu_id:
                ctx = (
                    conn.execute(
                        text(
                            """
                        SELECT m.id AS menu_id, m.name AS menu_name, m.price,
                               r.id AS restaurant_id, r.name AS restaurant_name,
                               r.building_id AS restaurant_building_id,
                               b1.name AS restaurant_building_name,
                               pb.id AS pickup_poi_id, pb.label AS pickup_poi_label,
                               db.id AS dropoff_building_id, db.name AS dropoff_building_name,
                               dp.id AS dropoff_poi_id, dp.label AS dropoff_poi_label
                        FROM menus m
                        JOIN restaurants r ON r.id = m.restaurant_id
                        JOIN buildings   b1 ON b1.id = r.building_id
                        JOIN pois pb ON pb.id = :pp
                        JOIN pois dp ON dp.id = :dp
                        JOIN buildings db ON db.id = dp.building_id
                        WHERE m.id = :mid
                        """
                        ),
                        {"pp": pickup_poi_id, "dp": dropoff_poi_id, "mid": menu_id},
                    )
                    .mappings()
                    .first()
                )
            else:
                # 메뉴 없이도 건물/POI 명은 채워주자
                ctx = (
                    conn.execute(
                        text(
                            """
                        SELECT
                          r.id  AS restaurant_id, r.name AS restaurant_name,
                          b1.id AS restaurant_building_id, b1.name AS restaurant_building_name,
                          pb.id AS pickup_poi_id, pb.label AS pickup_poi_label,
                          db.id AS dropoff_building_id, db.name AS dropoff_building_name,
                          dp.id AS dropoff_poi_id, dp.label AS dropoff_poi_label
                        FROM pois pb
                        JOIN buildings b1 ON b1.id = pb.building_id
                        JOIN pois dp ON dp.id = :dp
                        JOIN buildings db ON db.id = dp.building_id
                        LEFT JOIN restaurants r ON 1=0  -- 정보가 없으면 NULL 유지
                        WHERE pb.id = :pp
                        """
                        ),
                        {"pp": pickup_poi_id, "dp": dropoff_poi_id},
                    )
                    .mappings()
                    .first()
                )

            # 5) missions 생성 (※ updated_at 컬럼 없음!)
            row = conn.execute(
                text(
                    """
                    INSERT INTO missions
                    (user_msg, pickup_poi_id, dropoff_poi_id, restaurant_id, menu_id, status, created_at)
                    VALUES (:msg, :pp, :dp, :rid, :mid, 'queued', NOW())
                    """
                ),
                {
                    "msg": user_msg,
                    "pp": pickup_poi_id,
                    "dp": dropoff_poi_id,
                    "rid": restaurant_id,
                    "mid": menu_id,
                },
            )
            mission_id = row.lastrowid

            # 6) mission_points (선택) — 테이블 없을 수 있으니 안전 처리
            try:
                conn.execute(
                    text(
                        """
                        INSERT INTO mission_points (mission_id, seq, poi_id, action, payload_json)
                        VALUES
                        (:mid, 1, :pp, 'goto',    JSON_OBJECT()),
                        (:mid, 2, :pp, 'pickup',  JSON_OBJECT('confirm','menu_ready','menu_id',:mid_id,'menu_name',:mname,'price',:price)),
                        (:mid, 3, :dp, 'goto',    JSON_OBJECT()),
                        (:mid, 4, :dp, 'dropoff', JSON_OBJECT('handover','user_pickup'))
                        """
                    ),
                    {
                        "mid": mission_id,
                        "pp": pickup_poi_id,
                        "dp": dropoff_poi_id,
                        "mid_id": (ctx.get("menu_id") if ctx else menu_id),
                        "mname": (ctx.get("menu_name") if ctx else None),
                        "price": (ctx.get("price") if ctx else None),
                    },
                )
            except Exception:
                # mission_points 미구현/미생성 환경을 허용
                pass

            # 7) 최초 이벤트 기록 (mission_events.ts 사용)
            try:
                conn.execute(
                    text(
                        """
                        INSERT INTO mission_events (mission_id, phase, ts, note)
                        VALUES (:mid, 'QUEUED', NOW(), 'created by chatbot')
                        """
                    ),
                    {"mid": mission_id},
                )
            except Exception:
                # mission_events 테이블이 없을 수도 있음
                pass

            # 사용자 메시지 표기용 컨텍스트
            result_ctx = {
                "mission_id": mission_id,
                "restaurant_name": (ctx.get("restaurant_name") if ctx else None),
                "restaurant_building_name": (
                    ctx.get("restaurant_building_name") if ctx else None
                ),
                "dropoff_building_name": (
                    ctx.get("dropoff_building_name") if ctx else None
                ),
                "menu_name": (ctx.get("menu_name") if ctx else None),
                "price": (ctx.get("price") if ctx else None),
            }

            return {
                "ok": True,
                "mission_id": mission_id,
                "pickup_poi_id": pickup_poi_id,
                "dropoff_poi_id": dropoff_poi_id,
                "restaurant_id": restaurant_id,
                "menu_id": menu_id,
                "context": result_ctx,
            }

    return await asyncio.to_thread(_tx)


# ─────────────────────────────────────────────
# 진행 알림 메시지 포매터
# ─────────────────────────────────────────────

# 템플릿 키는 DB ENUM과 정규화된 이벤트명 사용
MISSION_EVENT_TEMPLATES: Dict[str, str] = {
    "ARRIVED_PICKUP": "{restaurant_building_name} 도착!\n로봇이 {restaurant_name}에서 음식을 픽업했어요.\n이제 {dropoff_building_name}으로 배송해드릴게요.\n조금만 기다려주세요!",
    "DONE": "음식 배송 완료했습니다!\n맛있게 드세요 😊",
}


def _normalize_phase(event_type: str) -> str:
    et = (event_type or "").upper().strip()
    mapping = {
        "ARRIVE_PICKUP": "ARRIVED_PICKUP",
        "ARRIVE_DROPOFF": "ARRIVED_DROPOFF",
        "DROPOFF_DONE": "DONE",
    }
    return mapping.get(et, et)


def get_mission_context(mission_id: int) -> Optional[Dict]:
    with _engine.begin() as conn:
        row = (
            conn.execute(
                text(
                    """
                SELECT m.id AS mission_id,
                       r.name AS restaurant_name,
                       b1.name AS restaurant_building_name,
                       b2.name AS dropoff_building_name
                FROM missions m
                LEFT JOIN restaurants r ON r.id = m.restaurant_id
                LEFT JOIN pois pp ON pp.id = m.pickup_poi_id
                LEFT JOIN buildings b1 ON b1.id = r.building_id
                LEFT JOIN pois dp ON dp.id = m.dropoff_poi_id
                LEFT JOIN buildings b2 ON b2.id = dp.building_id
                WHERE m.id = :mid
                """
                ),
                {"mid": mission_id},
            )
            .mappings()
            .first()
        )
        if not row:
            return None
        return dict(row)


def format_mission_event_message(event_type: str, mission_id: int) -> Optional[str]:
    """
    서버/로봇이 보고하는 이벤트를 사용자 안내 문구로 변환.
    event_type 예: "ARRIVE_PICKUP" | "ARRIVED_PICKUP" | "DONE" | "DROPOFF_DONE"
    """
    et = _normalize_phase(event_type)
    tmpl = MISSION_EVENT_TEMPLATES.get(et)
    if not tmpl:
        return None
    ctx = get_mission_context(mission_id)
    if not ctx:
        return None
    try:
        return tmpl.format(**ctx)
    except Exception:
        return None
