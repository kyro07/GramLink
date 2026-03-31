# routers/missed_call.py
# This is the MOST IMPORTANT endpoint
# Called by Infobip when someone gives a missed call

from fastapi import APIRouter, Request, BackgroundTasks
import json

router = APIRouter()

@router.post("/missed-call")
async def handle_missed_call(request: Request, background_tasks: BackgroundTasks):
    """
    Infobip calls this when a passenger gives a missed call.
    
    FLOW:
    Step 1 (0-2 sec)  → Detect missed call, extract phone number
    Step 2 (2-4 sec)  → Look up user in database
    Step 3 (4-6 sec)  → Calculate ETA using ML + GPS
    Step 4 (6-8 sec)  → Generate Tamil voice audio
    Step 5 (8-10 sec) → Auto-call passenger with audio
    """
    # Parse the webhook body from Infobip
    body = await request.json()
    
    # Extract caller's phone number
    caller_phone = body.get("from", body.get("callerNumber", ""))
    
    if not caller_phone:
        return {"status": "error", "message": "No phone number in webhook"}
    
    # Run the full flow in background (so we can respond to Infobip quickly)
    background_tasks.add_task(process_missed_call, caller_phone)
    
    # Immediately return 200 OK to Infobip
    return {"status": "received", "phone": caller_phone}


async def process_missed_call(phone: str):
    """Background task — full missed call processing"""
    from database.queries import get_user_by_phone, get_stop, get_buses_on_route, log_eta
    from services.eta_engine import calculate_eta
    from services.voice_generator import generate_eta_audio
    from services.infobip_service import make_voice_call, send_registration_sms
    
    # ── STEP 1: Check if user is registered ──────────────────
    user = get_user_by_phone(phone)
    
    if not user:
        # New user — send registration SMS
        await send_registration_sms(phone)
        return
    
    # ── STEP 2: Get user's stop and route ────────────────────
    stop = get_stop(user["stop_id"])
    buses = get_buses_on_route(user["route_id"])
    
    if not stop or not buses:
        # No active bus — send SMS
        from services.infobip_service import send_sms
        await send_sms(phone, 
            f"GramLink: Route {user['route_id']} bus is not active right now.")
        return
    
    # ── STEP 3: Calculate ETA ────────────────────────────────
    eta_result = await calculate_eta(
        stop_lat=stop["lat"],
        stop_lng=stop["lng"],
        route_id=user["route_id"],
        buses=buses
    )
    eta_minutes = eta_result["eta_minutes"]
    
    # Log the ETA for ML retraining
    log_eta(phone, user["route_id"], eta_minutes)
    
    # ── STEP 4: Generate Tamil voice audio ───────────────────
    # Tamil message: "Your 47C bus will come in 12 minutes. 32 seats available."
    tamil_text = (
        f"Ungal {user['route_id']} bus {eta_minutes} nimalathil varum. "
        f"{buses[0]['seats_available']} iruppidam ullo."
    )
    audio_file = await generate_eta_audio(tamil_text, phone)
    
    # ── STEP 5: Auto-call passenger ──────────────────────────
    await make_voice_call(phone, audio_file)
    
    print(f"✅ Processed missed call from {phone}: ETA = {eta_minutes} min")

