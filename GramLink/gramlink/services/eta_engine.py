# services/eta_engine.py
# Core ETA calculation combining GPS distance + ML delay prediction

import math
from typing import List, Dict
from services.ml_model import predict_delay


def haversine_distance(lat1: float, lng1: float, 
                        lat2: float, lng2: float) -> float:
    """
    Calculate straight-line distance between two GPS points.
    Uses Haversine formula.
    
    Returns: Distance in kilometers
    """
    R = 6371  # Earth radius in km
    
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c  # Distance in km


async def calculate_eta(stop_lat: float, stop_lng: float,
                         route_id: str, buses: List[Dict]) -> Dict:
    """
    Calculate ETA for bus to reach a specific stop.
    
    Algorithm:
    1. Find nearest bus (by GPS distance)
    2. Estimate time based on distance + current speed
    3. Add ML-predicted delay
    4. Return ETA in minutes
    
    Returns:
        {
            "eta_minutes": 12,
            "bus_id": "BUS001",
            "distance_km": 8.5,
            "confidence": 0.87
        }
    """
    if not buses:
        return {"eta_minutes": 999, "bus_id": None, "confidence": 0}
    
    best_eta = float("inf")
    best_bus = None
    best_distance = None
    
    for bus in buses:
        # Calculate distance from bus to stop
        distance_km = haversine_distance(
            bus["lat"], bus["lng"],
            stop_lat, stop_lng
        )
        
        # Get bus speed (minimum 10 km/h, maximum 60 km/h)
        speed_kmh = max(10, min(60, bus.get("speed", 20)))
        
        # Base ETA = distance / speed (in hours → convert to minutes)
        base_eta_min = (distance_km / speed_kmh) * 60
        
        # Add ML-predicted delay
        predicted_delay = predict_delay(route_id)
        
        # Total ETA
        total_eta = base_eta_min + predicted_delay
        
        if total_eta < best_eta:
            best_eta = total_eta
            best_bus = bus
            best_distance = distance_km
    
    # Round to nearest minute, minimum 1 minute
    eta_minutes = max(1, round(best_eta))
    
    # Confidence score (higher for closer buses)
    confidence = min(0.95, 1.0 - (best_distance / 50))  # 50km = 0% confidence
    
    return {
        "eta_minutes": eta_minutes,
        "bus_id": best_bus["bus_id"] if best_bus else None,
        "distance_km": round(best_distance, 2) if best_distance else None,
        "seats_available": best_bus.get("seats_available", "?") if best_bus else "?",
        "confidence": round(confidence, 2)
    }