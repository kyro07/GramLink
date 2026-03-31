# services/walk_alert.py
# Calculate walking time using OSRM (free, no API key needed)
# Check if passengers need a "time to leave home" alert

import requests
from typing import Tuple
from database.queries import get_supabase

def get_walk_time_minutes(home_coords: Tuple[float, float], 
                           stop_coords: Tuple[float, float]) -> int:
    """
    Calculate walking time from home to bus stop using OSRM.
    
    OSRM is a free routing engine using OpenStreetMap data.
    No API key required!
    
    Args:
        home_coords: (lat, lng) of passenger's home
        stop_coords: (lat, lng) of bus stop
        
    Returns:
        Walking time in minutes (rounded up)
    """
    try:
        home_lat, home_lng = home_coords
        stop_lat, stop_lng = stop_coords
        
        # OSRM API format: /route/v1/{profile}/{lng,lat};{lng,lat}
        base_url = "https://router.project-osrm.org/route/v1/foot"
        url = f"{base_url}/{home_lng},{home_lat};{stop_lng},{stop_lat}"
        
        response = requests.get(
            url,
            params={"overview": "false"},  # We only need duration, not route path
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            duration_seconds = data["routes"][0]["duration"]
            # Convert to minutes, always round UP
            return int(duration_seconds / 60) + 1
        else:
            # Fallback: use user's self-reported walk time
            return 10
            
    except requests.Timeout:
        print("⚠️ OSRM timeout. Using default 10 minutes.")
        return 10
    except Exception as e:
        print(f"⚠️ OSRM error: {e}")
        return 10


def should_alert(user: dict, current_bus_eta: int) -> bool:
    """
    Decide if we should send a walk alert to this passenger.
    
    Alert if: bus_eta <= walk_time + buffer + 2 minutes
    
    Example:
    - walk_time = 8 minutes
    - buffer = 5 minutes
    - threshold = 8 + 5 + 2 = 15 minutes
    - If bus is 14 minutes away → ALERT!
    - If bus is 20 minutes away → no alert yet
    """
    threshold = user["walk_minutes"] + user["buffer_mins"] + 2
    return current_bus_eta <= threshold


async def check_and_send_walk_alerts(route_id: str, bus_id: str):
    """
    Check all users on a route and send walk alerts if needed.
    Called every time a driver sends a GPS ping.
    """
    from database.queries import get_stop, get_buses_on_route, log_alert
    from services.eta_engine import calculate_eta
    from services.infobip_service import send_sms
    
    db = get_supabase()
    
    # Get all users on this route
    users_result = db.table("users").select("*").eq("route_id", route_id).execute()
    users = users_result.data
    
    if not users:
        return
    
    # Get buses on route
    buses = get_buses_on_route(route_id)
    if not buses:
        return
    
    for user in users:
        try:
            # Get their stop
            stop = get_stop(user["stop_id"])
            if not stop:
                continue
            
            # Calculate ETA for this user's stop
            eta_result = await calculate_eta(
                stop_lat=stop["lat"],
                stop_lng=stop["lng"],
                route_id=route_id,
                buses=buses
            )
            eta_minutes = eta_result["eta_minutes"]
            
            # Calculate actual walk time using OSRM
            walk_time = get_walk_time_minutes(
                home_coords=(user["home_lat"], user["home_lng"]),
                stop_coords=(stop["lat"], stop["lng"])
            )
            
            # Should we alert?
            if should_alert(user, eta_minutes):
                # Tamil SMS: "Come out! 47C bus comes in 12 min. Walk 8 min."
                msg = (
                    f"Vandha padunga! {route_id} bus {eta_minutes} nimalathil varum. "
                    f"Neenga {walk_time} nimidangalil nadakanum."
                )
                await send_sms(user["phone"], msg)
                log_alert(user["phone"], "sms", eta_minutes, walk_time)
                
        except Exception as e:
            print(f"Alert error for {user['phone']}: {e}")
            continue