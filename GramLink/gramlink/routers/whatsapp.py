# routers/whatsapp.py
from fastapi import APIRouter, Request, BackgroundTasks

router = APIRouter()

@router.post("/whatsapp")
async def handle_whatsapp(request: Request, background_tasks: BackgroundTasks):
    """
    Called by Infobip when a WhatsApp message is received.
    
    Handles Tamil/Tanglish messages like:
    - "47C bus eppo varum?" (When will 47C bus come?)
    - "Bus seat iruka?" (Are seats available?)
    """
    body = await request.json()
    
    sender_phone = body.get("from", "")
    message_text = body.get("text", {}).get("body", "")
    
    if not sender_phone or not message_text:
        return {"status": "ignored"}
    
    background_tasks.add_task(process_whatsapp, sender_phone, message_text)
    return {"status": "received"}


async def process_whatsapp(phone: str, message: str):
    """Process WhatsApp message and respond"""
    from services.tamil_nlp import parse_intent, transliterate_tamil
    from database.queries import get_user_by_phone, get_stop, get_buses_on_route
    from services.eta_engine import calculate_eta
    from services.voice_generator import generate_eta_audio
    from services.infobip_service import send_whatsapp_voice_note, send_whatsapp_text
    
    # Detect intent from Tamil/Tanglish message
    intent = parse_intent(message)
    
    user = get_user_by_phone(phone)
    if not user:
        await send_whatsapp_text(phone, 
            "GramLink-il register pannum: STOP <stop_id> ROUTE <route_id> anupunga")
        return
    
    if intent["intent"] == "eta":
        stop = get_stop(user["stop_id"])
        buses = get_buses_on_route(user["route_id"])
        
        if not buses:
            await send_whatsapp_text(phone, "Bus ippo active illa. Mela pathunga.")
            return
        
        eta_result = await calculate_eta(
            stop_lat=stop["lat"],
            stop_lng=stop["lng"],
            route_id=user["route_id"],
            buses=buses
        )
        
        eta_minutes = eta_result["eta_minutes"]
        tamil_text = f"Ungal {user['route_id']} bus {eta_minutes} nimalathil varum."
        
        # Send voice note on WhatsApp
        audio_file = await generate_eta_audio(tamil_text, f"wa_{phone}")
        await send_whatsapp_voice_note(phone, audio_file, tamil_text)
    
    elif intent["intent"] == "seats":
        buses = get_buses_on_route(user["route_id"])
        if buses:
            seats = buses[0]["seats_available"]
            await send_whatsapp_text(phone, f"{user['route_id']} bus-la {seats} seats iruku.")
        else:
            await send_whatsapp_text(phone, "Bus position kedaikala.")

    elif intent["intent"] == "status":
        buses = get_buses_on_route(user["route_id"])
        status = "running" if buses else "not active"
        await send_whatsapp_text(phone, f"{user['route_id']} bus ippo {status}.")