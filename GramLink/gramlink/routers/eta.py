# routers/eta.py
from fastapi import APIRouter, HTTPException
from database.queries import get_stop, get_buses_on_route
from services.eta_engine import calculate_eta

router = APIRouter()

@router.get("/eta/{stop_id}/{route_id}")
async def get_eta(stop_id: str, route_id: str):
    """
    Get predicted ETA for a bus at a specific stop.
    
    Example: GET /eta/GANAPATHY/47C
    Returns: {"eta_minutes": 12, "bus_id": "BUS001", "confidence": 0.87}
    """
    # Get stop coordinates
    stop = get_stop(stop_id)
    if not stop:
        raise HTTPException(status_code=404, detail=f"Stop '{stop_id}' not found")
    
    # Get active buses on route
    buses = get_buses_on_route(route_id)
    if not buses:
        raise HTTPException(status_code=404, 
                          detail=f"No active buses on route '{route_id}'")
    
    # Calculate ETA using ML + distance
    eta_result = await calculate_eta(
        stop_lat=stop["lat"],
        stop_lng=stop["lng"],
        route_id=route_id,
        buses=buses
    )
    
    return eta_result

@router.get("/buses/{route_id}")
async def get_route_buses(route_id: str):
    """Get all active buses on a route with their live positions"""
    buses = get_buses_on_route(route_id)
    return {
        "route_id": route_id,
        "active_buses": len(buses),
        "buses": buses
    }