# app/orders.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Tuple
from app.db_mission import create_mission_from_selection

router = APIRouter(prefix="/order", tags=["order"])


class OrderConfirmBody(BaseModel):
    user_msg: str
    menu_id: Optional[int] = None
    restaurant_id: Optional[int] = None
    pickup_poi_id: Optional[int] = None
    dropoff_poi_id: Optional[int] = None
    user_xy: Optional[Tuple[float, float]] = None  # [x,y] or null


@router.post("/confirm")
async def order_confirm(body: OrderConfirmBody):
    res = await create_mission_from_selection(
        user_msg=body.user_msg,
        menu_id=body.menu_id,
        restaurant_id=body.restaurant_id,
        pickup_poi_id=body.pickup_poi_id,
        dropoff_poi_id=body.dropoff_poi_id,
        user_xy=body.user_xy,
    )
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error", "unknown"))
    return res
