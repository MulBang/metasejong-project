from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.session import db_conn  # SQLAlchemy 세션 컨텍스트

router = APIRouter()


class RouteReq(BaseModel):
    start_label: str
    goal_label: str
    max_depth: int = 50


def compute_route(start_label: str, goal_label: str, max_depth: int = 50) -> dict:
    from db.session import db_conn
    from fastapi import HTTPException

    if max_depth < 1 or max_depth > 200:
        raise HTTPException(status_code=400, detail="max_depth out of range (1~200)")

    with db_conn() as conn:
        raw = conn.connection
        cur = raw.cursor()
        try:
            cur.execute("SET @start_label := %s", (start_label,))
            cur.execute("SET @goal_label := %s", (goal_label,))
            cur.execute("SET @start := (SELECT id FROM nodes WHERE label=@start_label)")
            cur.execute("SET @goal  := (SELECT id FROM nodes WHERE label=@goal_label)")
            cur.execute(
                """
                WITH RECURSIVE
                paths(n, path_ids, path_labels, cost, depth) AS (
                  SELECT
                    @start,
                    CAST(@start AS CHAR(1000)),
                    (SELECT label FROM nodes WHERE id=@start),
                    CAST(0 AS DOUBLE),   
                    0
                  UNION ALL
                  SELECT
                    e.b,
                    CONCAT(paths.path_ids, ',', e.b),
                    CONCAT(paths.path_labels, ' -> ', (SELECT label FROM nodes WHERE id=e.b)),
                    CAST(paths.cost + e.w AS DOUBLE),
                    depth + 1
                  FROM edges_u e
                  JOIN paths ON e.a = paths.n
                  WHERE depth < %s AND FIND_IN_SET(e.b, paths.path_ids) = 0
                )
                SELECT path_labels AS route, ROUND(cost,3) AS total_distance
                FROM paths
                WHERE n = @goal
                ORDER BY cost
                LIMIT 1
                """,
                (max_depth,),
            )
            row = cur.fetchone()
        finally:
            cur.close()

    if not row:
        raise HTTPException(status_code=404, detail="no route found (check labels)")
    return {"route": row[0], "total_distance": float(row[1])}


@router.post("/route")
async def route(req: RouteReq):
    return compute_route(req.start_label, req.goal_label, req.max_depth)
