# routers/register.py
from fastapi import APIRouter, HTTPException
from models.schemas import RegisterUser
from database.queries import get_user_by_phone, create_user

router = APIRouter()

@router.post("/register")
async def register_user(data: RegisterUser):
    """
    Register a new passenger with their home location and bus stop.
    
    This is called when:
    - User sends a WhatsApp message with their details
    - User replies to registration SMS
    """
    # Check if already registered
    existing = get_user_by_phone(data.phone)
    if existing:
        return {
            "message": "Already registered",
            "user": existing
        }
    
    # Create new user
    user = create_user(
        phone=data.phone,
        stop_id=data.stop_id,
        route_id=data.route_id,
        home_lat=data.home_lat,
        home_lng=data.home_lng,
        walk_minutes=data.walk_minutes,
        buffer_mins=data.buffer_mins
    )
    
    return {
        "message": "Registered successfully",
        "user": user
    }

@router.get("/user/{phone}")
async def get_user(phone: str):
    """Get user profile by phone number"""
    user = get_user_by_phone(phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

