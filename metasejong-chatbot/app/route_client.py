# app/route_client.py
import httpx
from typing import Dict, Any, Optional

ROUTE_BASE = "http://127.0.0.1:9000"  # 메타세종-서버(라우팅) 주소로 바꿔줘


async def get_route_leg(src_poi: str, dst_poi: str) -> Dict[str, Any]:
    """
    src_poi, dst_poi는 POI의 label 또는 node_id 등
    라우팅 서버가 요구하는 식별자 형식으로 맞춰 전달.
    서버가 GET인지 POST인지에 맞춰 수정.
    """
    # 예시: GET /route?src=Chungmu%20entrance&dst=Yeongsil%20entrance
    url = f"{ROUTE_BASE}/route"
    params = {"src": src_poi, "dst": dst_poi}
    async with httpx.AsyncClient(timeout=10.0) as cli:
        r = await cli.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        # 기대 예: {"route":"Chungmu -> Yeongsil","total_distance":26.854, "waypoints":[...]}
        return {
            "summary": data.get("route"),
            "distance": float(data.get("total_distance", 0.0)),
            "waypoints": data.get("waypoints") or [],
        }


def estimate_eta_sec(distance_m: float, speed_mps: float = 0.8) -> int:
    # 단순 ETA (속도는 로봇 실측값으로 조정)
    return int(distance_m / max(speed_mps, 0.1))
