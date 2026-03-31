# models/schemas.py
# Pydantic models — these define the shape of data in API requests

from pydantic import BaseModel
from typing import Optional

class MissedCallWebhook(BaseModel):
    """Data Infobip sends when someone makes a missed call"""
    from_: str        # Caller's phone number
    to: str           # GramLink number they called
    callId: str       # Unique call ID
    direction: str = "INBOUND"

class WhatsAppWebhook(BaseModel):
    """Data Infobip sends when WhatsApp message received"""
    from_: str         # Sender phone
    to: str            # GramLink WhatsApp number
    message: str       # Message text (Tamil/Tanglish)
    messageId: str

class DriverPing(BaseModel):
    """GPS data from Flutter driver app"""
    bus_id: str           # Bus number (e.g., "BUS001")
    route_id: str         # Route (e.g., "47C")
    lat: float            # Latitude
    lng: float            # Longitude
    speed: float = 0.0    # Speed in km/h
    seats_available: int = 40  # Empty seats

class RegisterUser(BaseModel):
    """New user registration data"""
    phone: str
    stop_id: str
    route_id: str
    home_lat: float
    home_lng: float
    walk_minutes: int = 10
    buffer_mins: int = 5

class FeedbackData(BaseModel):
    """User feedback on ETA accuracy"""
    phone: str
    log_id: str
    actual_eta: int       # How many minutes bus actually took
    rating: int           # 1-5 stars