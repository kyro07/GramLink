# services/infobip_service.py
# All Infobip API calls: SMS, Voice, WhatsApp

import os
import requests
import base64
from pathlib import Path

INFOBIP_BASE_URL = os.getenv("4kedp8.api.infobip.com")
INFOBIP_API_KEY = os.getenv("e361e75db8cf68942b8c9264e6157d73-ce821ae4-265e-4d37-bab1-bfc4663d7fc7")
INFOBIP_SENDER = os.getenv("447860088970", "GramLink")
INFOBIP_WA_NUMBER = os.getenv("+44 7860 088970")

# Common headers for all Infobip API calls
HEADERS = {
    "Authorization": f"App e361e75db8cf68942b8c9264e6157d73-ce821ae4-265e-4d37-bab1-bfc4663d7fc7",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


async def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS to a phone number.
    Works on any phone (feature phone or smartphone).
    
    Returns True if sent successfully.
    """
    url = f"https://4kedp8.api.infobip.com/sms/2/text/advanced"
    
    payload = {
        "messages": [{
            "from": INFOBIP_SENDER,
            "destinations": [{"to": phone}],
            "text": message
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ SMS sent to {phone}")
            return True
        else:
            print(f"❌ SMS failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False


async def make_voice_call(phone: str, audio_file_path: str) -> bool:
    """
    Auto-call a passenger and play Tamil voice audio.
    
    This is the KEY feature — zero cost for passenger (missed call → callback)
    
    Steps:
    1. Read MP3 file
    2. Convert to base64
    3. Send to Infobip Voice API
    4. Infobip calls the passenger
    5. Passenger hears Tamil ETA message
    """
    url = f"https://4kedp8.api.infobip.com/voice/1/dial"
    
    try:
        # Read and encode audio file
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            print(f"❌ Audio file not found: {audio_file_path}")
            return False
        
        with open(audio_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        payload = {
            "from": INFOBIP_SENDER,
            "to": phone,
            "callTimeout": 30,
            "deliveryTimeWindow": {
                "from": {"hour": 6, "minute": 0},
                "to": {"hour": 22, "minute": 0}
            },
            "machineDetection": "CONTINUE",
            "record": False,
            "callTransfers": [],
            "voice": {
                "name": "Aditi",    # Indian female voice
                "language": "ta-IN" # Tamil India
            },
            "audioFileData": {
                "audioFileContent": audio_base64,
                "audioFileContentType": "audio/mp3"
            }
        }
        
        response = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        
        if response.status_code in [200, 201]:
            print(f"✅ Voice call initiated to {phone}")
            return True
        else:
            print(f"❌ Voice call failed: {response.status_code} - {response.text}")
            # Fallback to SMS
            await send_sms(phone, "GramLink: Check your bus ETA. Reply 'BUS' for update.")
            return False
            
    except Exception as e:
        print(f"❌ Voice call error: {e}")
        return False


async def send_registration_sms(phone: str) -> bool:
    """Send registration instructions to new users"""
    message = (
        "Welcome to GramLink! Register pannunga: "
        "Reply: STOP <stop_name> ROUTE <route_number> "
        "Example: STOP GANAPATHY ROUTE 47C"
    )
    return await send_sms(phone, message)


async def send_whatsapp_text(phone: str, message: str) -> bool:
    """Send a text message on WhatsApp"""
    url = f"https://4kedp8.api.infobip.com/whatsapp/1/message/text"
    
    payload = {
        "from": INFOBIP_WA_NUMBER,
        "to": phone,
        "content": {
            "text": message
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"❌ WhatsApp text error: {e}")
        return False


async def send_whatsapp_voice_note(phone: str, 
                                    audio_file_path: str, 
                                    caption: str = "") -> bool:
    """Send a voice note on WhatsApp with the Tamil ETA audio"""
    url = f"https://4kedp8.api.infobip.com/whatsapp/1/message/audio"
    
    try:
        # Upload audio and get URL first
        # For simplicity, we'll use the text API as fallback
        return await send_whatsapp_text(phone, caption)
    except Exception as e:
        print(f"❌ WhatsApp voice note error: {e}")
        return False

