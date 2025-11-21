# app/db.py
import asyncio, os
from dotenv import load_dotenv  # .env 파일을 읽는 시점을 명시적으로 추가
from sqlalchemy import create_engine, text
from typing import List, Dict, Optional, Tuple


load_dotenv()  # .env 파일에서 환경변수 로드

DB_URL = os.getenv("DB_URL")
_engine = create_engine(DB_URL, pool_pre_ping=True, future=True)


async def get_dropoff_buildings() -> List[Dict]:
    def _q():
        with _engine.connect() as c:
            rows = (
                c.execute(
                    text(
                        """
                SELECT id, name FROM buildings
                WHERE role='dropoff'
                ORDER BY id
            """
                    )
                )
                .mappings()
                .all()
            )
            return [dict(r) for r in rows]

    return await asyncio.to_thread(_q)


async def validate_dropoff_name(name: str) -> Optional[Dict]:
    """사용자 응답이 드롭오프 건물 중 하나인지 확인"""

    def _q():
        with _engine.connect() as c:
            r = (
                c.execute(
                    text(
                        """
                SELECT id, name FROM buildings
                WHERE role='dropoff' AND (name LIKE :n OR name = :eqn)
                ORDER BY id LIMIT 1
            """
                    ),
                    {"n": f"%{name}%", "eqn": name},
                )
                .mappings()
                .first()
            )
            return dict(r) if r else None

    return await asyncio.to_thread(_q)


async def search_menus_by_keywords_joined(
    keywords: List[str], top_k: int = 8
) -> List[Dict]:
    """DB 전용 추천: menus + restaurants + buildings 조인"""
    if not keywords:
        return []

    def _q():
        with _engine.connect() as c:
            like = " OR ".join([f"m.name LIKE :kw{i}" for i in range(len(keywords))])
            sql = f"""
                SELECT
                  m.id AS menu_id, m.name AS menu_name, m.price,
                  r.id AS restaurant_id, r.name AS restaurant_name,
                  b.id AS building_id,  b.name AS building_name
                FROM menus m
                JOIN restaurants r ON r.id = m.restaurant_id
                JOIN buildings   b ON b.id = r.building_id
                WHERE {like}
                ORDER BY b.id, r.id, m.id
                LIMIT :k
            """
            params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
            params["k"] = top_k
            rows = c.execute(text(sql), params).mappings().all()
            return [dict(r) for r in rows]

    return await asyncio.to_thread(_q)


async def ping_db():
    try:

        def _q():
            with _engine.connect() as c:
                # 가장 안전한 헬스체크: 있는 테이블 아무거나 하나 count
                # 우선순위: menus가 있으면 menus, 없으면 pois
                try:
                    n = c.execute(text("SELECT COUNT(*) FROM menus")).scalar_one()
                    return {"ok": True, "table": "menus", "count": int(n)}
                except Exception:
                    n = c.execute(text("SELECT COUNT(*) FROM pois")).scalar_one()
                    return {"ok": True, "table": "pois", "count": int(n)}

        return await asyncio.to_thread(_q)
    except Exception as e:
        return {"ok": False, "error": str(e)}


# app/db.py (추가)
# 추가: 메뉴 후보 (조인 + 폴백)
async def search_menu_candidates(q: str, top_k: int = 5):
    def _q():
        with _engine.connect() as c:
            rows = (
                c.execute(
                    text(
                        """
                    SELECT 
                      m.id   AS menu_id,   m.name AS menu_name, m.price,
                      r.id   AS restaurant_id, r.name AS restaurant_name, r.category,
                      b.id   AS building_id,   b.name AS building_name
                    FROM menus m
                    JOIN restaurants r ON r.id = m.restaurant_id
                    JOIN buildings   b ON b.id = r.building_id
                    WHERE m.name LIKE :kw
                       OR r.name LIKE :kw
                       OR r.category LIKE :kw
                       OR b.name LIKE :kw
                    ORDER BY m.id
                    LIMIT :k
                """
                    ),
                    {"kw": f"%{q}%", "k": top_k},
                )
                .mappings()
                .all()
            )
            if rows:
                return list(rows)
            # 폴백: 아무 것도 안 맞으면 최근/ID순 상위 N개
            rows = (
                c.execute(
                    text(
                        """
                    SELECT 
                      m.id   AS menu_id,   m.name AS menu_name, m.price,
                      r.id   AS restaurant_id, r.name AS restaurant_name, r.category,
                      b.id   AS building_id,   b.name AS building_name
                    FROM menus m
                    JOIN restaurants r ON r.id = m.restaurant_id
                    JOIN buildings   b ON b.id = r.building_id
                    ORDER BY m.id DESC
                    LIMIT :k
                """
                    ),
                    {"k": top_k},
                )
                .mappings()
                .all()
            )
            return list(rows)

    return await asyncio.to_thread(_q)


async def search_menus_by_keywords(keywords: List[str], top_k: int = 8) -> List[Dict]:
    """
    여러 키워드로 menus.name을 LIKE 검색하고,
    restaurants/buildings 조인해서 건물/식당명까지 함께 반환.
    결과가 전부 DB에서 온 것이므로 'DB only' 보장이 됨.
    """
    if not keywords:
        return []

    def _q():
        with _engine.connect() as c:
            # WHERE (m.name LIKE :kw1 OR m.name LIKE :kw2 OR ...)
            like_clauses = " OR ".join(
                [f"m.name LIKE :kw{i}" for i in range(len(keywords))]
            )
            sql = f"""
                SELECT
                    m.id         AS menu_id,
                    m.name       AS menu_name,
                    m.price      AS price,
                    r.id         AS restaurant_id,
                    r.name       AS restaurant_name,
                    r.category   AS restaurant_category,
                    b.id         AS building_id,
                    b.name       AS building_name
                FROM menus m
                JOIN restaurants r ON r.id = m.restaurant_id
                JOIN buildings   b ON b.id = r.building_id
                WHERE {like_clauses}
                ORDER BY b.id, r.id, m.id
                LIMIT :k
            """
            params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
            params["k"] = top_k
            rows = c.execute(text(sql), params).mappings().all()
            return [dict(r) for r in rows]

    return await asyncio.to_thread(_q)


# app/db.py (교체/개선)
async def search_menus_like(q: str, top_k: int = 5):
    def _q():
        try:
            with _engine.connect() as c:
                rows = (
                    c.execute(
                        text(
                            """
                        SELECT
                          m.id            AS id,
                          m.name          AS menu,
                          m.price         AS price,
                          r.id            AS restaurant_id,
                          r.name          AS restaurant,
                          r.category      AS category,
                          b.id            AS building_id,
                          b.name          AS building
                        FROM menus m
                        JOIN restaurants r ON r.id = m.restaurant_id
                        JOIN buildings   b ON b.id = r.building_id
                        WHERE m.name LIKE :kw
                           OR r.name LIKE :kw
                           OR b.name LIKE :kw
                           OR r.category LIKE :kw
                        LIMIT :k
                        """
                        ),
                        {"kw": f"%{q}%", "k": top_k},
                    )
                    .mappings()
                    .all()
                )
                # 키 이름을 rag_min과 맞춰 통일
                out = []
                for r in rows:
                    out.append(
                        {
                            "id": r["id"],
                            "name": r["menu"],
                            "price": r["price"],
                            "category": r.get("category", ""),
                            "restaurant_id": r["restaurant_id"],
                            "vendor": r["restaurant"],  # ← 식당명은 vendor 키로
                            "building_id": r["building_id"],
                            "building": r["building"],
                        }
                    )
                return out
        except Exception:
            return []

    return await asyncio.to_thread(_q)


# app/db.py (기존 search_pois_like를 이렇게 강화)
async def search_pois_like(q: str, top_k: int = 5):
    def _q():
        with _engine.connect() as c:
            rows = (
                c.execute(
                    text(
                        """
                        SELECT 
                            p.id, p.label, p.x, p.y, p.node_id,
                            b.id AS building_id, b.name AS building_name
                        FROM pois p
                        JOIN buildings b ON b.id = p.building_id
                        WHERE p.label LIKE :kw OR b.name LIKE :kw
                        ORDER BY p.id
                        LIMIT :k
                    """
                    ),
                    {"kw": f"%{q}%", "k": top_k},
                )
                .mappings()
                .all()
            )
            if rows:
                return list(rows)
            # 폴백: 그냥 앞에서 N개
            rows = (
                c.execute(
                    text(
                        """
                        SELECT 
                            p.id, p.label, p.x, p.y, p.node_id,
                            b.id AS building_id, b.name AS building_name
                        FROM pois p
                        JOIN buildings b ON b.id = p.building_id
                        ORDER BY p.id
                        LIMIT :k
                    """
                    ),
                    {"k": top_k},
                )
                .mappings()
                .all()
            )
            return list(rows)

    return await asyncio.to_thread(_q)


def _format_context(vec_snips: List[str], menu_rows, poi_rows) -> str:
    parts = []
    if vec_snips:
        parts.append("### 문서 스니펫\n" + "\n".join(f"- {s}" for s in vec_snips))

    if menu_rows:
        parts.append(
            "### 메뉴 후보 (이 목록 중에서만 선택)\n"
            + "\n".join(
                f"- 메뉴ID:{r['id']} | 건물:{r.get('building','')} | 식당:{r.get('vendor','')} | "
                f"메뉴:{r.get('name','')} | 가격:{r.get('price','')} | 분류:{r.get('category','')}"
                for r in menu_rows
            )
        )

    if poi_rows:
        parts.append(
            "### 위치 후보 (이 목록 중에서만 선택)\n"
            + "\n".join(
                f"- POI:{r['id']} | 건물:{r.get('building','')} | 라벨:{r.get('label','')} | 좌표:({r.get('x')},{r.get('y')})"
                for r in poi_rows
            )
        )
    return "\n\n".join(parts) if parts else "(컨텍스트 없음)"


async def find_menu_by_name_fragment(text_query: str, top_k: int = 5) -> Optional[Dict]:
    """
    사용자가 문장으로 답한 경우(예: '오므라이스 먹고싶어')에도
    menus.name LIKE 검색으로 가장 유사한 메뉴 1개를 반환.
    (레스토랑/건물까지 조인해서 넘겨줌)
    """
    q = text_query.strip()
    if not q:
        return None

    def _q():
        with _engine.connect() as cx:
            # 간단한 LIKE + 점수식: (이름에 포함되면 가점) + 짧을수록 우선
            # 필요하면 INSTR/LOCATE, SOUNDEX 등을 추가해도 됨
            sql = """
            SELECT
              m.id   AS menu_id,     m.name  AS menu_name,   m.price,
              r.id   AS restaurant_id, r.name AS restaurant_name, r.category AS restaurant_category,
              b.id   AS building_id, b.name AS building_name,
              -- 간단 점수: 포함되면 +100, 길이가 짧을수록 우선
              (CASE WHEN m.name LIKE :kw THEN 100 ELSE 0 END) - CHAR_LENGTH(m.name) AS score
            FROM menus m
            JOIN restaurants r ON r.id = m.restaurant_id
            JOIN buildings   b ON b.id = r.building_id
            WHERE m.name LIKE :kw OR r.name LIKE :kw OR b.name LIKE :kw
            ORDER BY score DESC, m.id ASC
            LIMIT :k
            """
            rows = cx.execute(text(sql), {"kw": f"%{q}%", "k": top_k}).mappings().all()
            return dict(rows[0]) if rows else None

    return await asyncio.to_thread(_q)
