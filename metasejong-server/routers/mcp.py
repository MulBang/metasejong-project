from fastapi import APIRouter, HTTPException
from routers.graph import compute_route  # graph.py에서 함수 가져옴

router = APIRouter()


@router.post("/mcp")
async def mcp_entry(payload: dict):
    """
    MCP (Model Context Protocol) 요청 처리용 엔드포인트
    """
    action = payload.get("action")
    params = payload.get("params", {}) or {}

    if action == "ping":
        return {"ok": True, "data": {"status": "pong"}}

    if action == "get_route":
        try:
            res = compute_route(
                start_label=params["start_label"],
                goal_label=params["goal_label"],
                max_depth=params.get("max_depth", 50),
            )
            return {"ok": True, "data": res}
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"missing param: {e.args[0]}")
    raise HTTPException(status_code=400, detail="unknown action")
