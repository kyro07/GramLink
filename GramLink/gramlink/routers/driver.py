# routers/driver.py
from fastapi import APIRouter
from models.schemas import DriverPing
from database.queries import update_bus_position
from services.walk_alert import check_and_send_walk_alerts

router = APIRouter()

@router.post("/driver/ping")
async def driver_ping(data: DriverPing):
    """
    Receives GPS ping from Flutter driver app every 30 seconds.
    
    Steps:
    1. Save bus position to Supabase
    2. Check if any passengers need walk alerts
    3. Return success
    """
    # Step 1: Save GPS position
    position = update_bus_position(
        bus_id=data.bus_id,
        route_id=data.route_id,
        lat=data.lat,
        lng=data.lng,
        speed=data.speed,
        seats_available=data.seats_available
    )
    
    # Step 2: Check walk alerts for all users on this route
    # This runs in the background (non-blocking)
    await check_and_send_walk_alerts(data.route_id, data.bus_id)
    
    return {
        "status": "position_saved",
        "bus_id": data.bus_id,
        "lat": data.lat,
        "lng": data.lng
    }