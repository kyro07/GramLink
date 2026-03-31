# database/queries.py
# All database query functions in one place

from database.supabase_client import get_supabase
from typing import Optional, List, Dict, Any

db = get_supabase()

# ─────────────────────────────────────────────
# USER QUERIES
# ─────────────────────────────────────────────

def get_user_by_phone(phone: str) -> Optional[Dict]:
    """
    Find a user by their phone number.
    Returns user data dict or None if not found.
    """
    result = db.table("users").select("*").eq("phone", phone).execute()
    if result.data:
        return result.data[0]  # Return first match
    return None

def create_user(phone: str, stop_id: str, route_id: str, 
                home_lat: float, home_lng: float,
                walk_minutes: int = 10, buffer_mins: int = 5) -> Dict:
    """Register a new user in the database"""
    data = {
        "phone": phone,
        "stop_id": stop_id,
        "route_id": route_id,
        "home_lat": home_lat,
        "home_lng": home_lng,
        "walk_minutes": walk_minutes,
        "buffer_mins": buffer_mins
    }
    result = db.table("users").insert(data).execute()
    return result.data[0]

# ─────────────────────────────────────────────
# BUS POSITION QUERIES
# ─────────────────────────────────────────────

def get_latest_bus_position(bus_id: str) -> Optional[Dict]:
    """Get the most recent GPS position of a specific bus"""
    result = (db.table("bus_positions")
              .select("*")
              .eq("bus_id", bus_id)
              .order("timestamp", desc=True)
              .limit(1)
              .execute())
    if result.data:
        return result.data[0]
    return None

def get_buses_on_route(route_id: str) -> List[Dict]:
    """Get all active buses on a route (last 5 minutes)"""
    from datetime import datetime, timedelta, timezone
    
    # Only get positions from last 5 minutes (active buses)
    five_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    
    result = (db.table("bus_positions")
              .select("*")
              .eq("route_id", route_id)
              .gte("timestamp", five_min_ago)
              .order("timestamp", desc=True)
              .execute())
    return result.data

def update_bus_position(bus_id: str, route_id: str, lat: float, 
                         lng: float, speed: float, seats_available: int) -> Dict:
    """Insert new GPS position for a bus"""
    data = {
        "bus_id": bus_id,
        "route_id": route_id,
        "lat": lat,
        "lng": lng,
        "speed": speed,
        "seats_available": seats_available
    }
    result = db.table("bus_positions").insert(data).execute()
    return result.data[0]

# ─────────────────────────────────────────────
# STOP QUERIES
# ─────────────────────────────────────────────

def get_stop(stop_id: str) -> Optional[Dict]:
    """Get stop details by stop_id"""
    result = db.table("stops").select("*").eq("stop_id", stop_id).execute()
    if result.data:
        return result.data[0]
    return None

# ─────────────────────────────────────────────
# ETA LOG QUERIES
# ─────────────────────────────────────────────

def log_eta(phone: str, route_id: str, predicted_eta: int) -> Dict:
    """Save an ETA prediction to database (for ML retraining)"""
    data = {
        "phone": phone,
        "route_id": route_id,
        "predicted_eta": predicted_eta
    }
    result = db.table("eta_logs").insert(data).execute()
    return result.data[0]

def get_historical_delays(route_id: str) -> List[Dict]:
    """Get past ETA logs for a route (used to train ML model)"""
    result = (db.table("eta_logs")
              .select("*")
              .eq("route_id", route_id)
              .not_.is_("actual_eta", "null")
              .order("timestamp", desc=True)
              .limit(500)
              .execute())
    return result.data

# ─────────────────────────────────────────────
# ALERT LOG QUERIES
# ─────────────────────────────────────────────

def log_alert(phone: str, alert_type: str, bus_eta: int, walk_time: int) -> Dict:
    """Record that we sent an alert to a passenger"""
    data = {
        "phone": phone,
        "alert_type": alert_type,
        "bus_eta": bus_eta,
        "walk_time": walk_time
    }
    result = db.table("alerts_sent").insert(data).execute()
    return result.data[0]