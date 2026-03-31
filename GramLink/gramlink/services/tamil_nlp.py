# services/tamil_nlp.py
# Tamil language processing using Shunya Labs Vak API

import os
import requests
from typing import Dict

VAK_API_URL = os.getenv("VAK_API_URL", "https://playground.shunyalabs.ai")
VAK_API_KEY = os.getenv("VAK_API_KEY", "LAiZ7SrRLcOFTSadCTKulh2kcqld4AZI")


def transliterate_tamil(text: str) -> str:
    """
    Convert Tamil or Tanglish text to English letters.
    
    Example:
    Input:  "47C bus eppo varum"  (Tanglish)
    Output: "47C bus eppo varum"  (same, already roman)
    
    Input:  "பஸ் எப்போ வரும்"  (Tamil script)
    Output: "bus eppo varum"     (romanized)
    """
    if not VAK_API_KEY:
        # Fallback: return as-is if no API key
        return text.lower()
    
    try:
        response = requests.post(
            f"{VAK_API_URL}/transliterate",
            json={
                "text": text,
                "src_lang": "ta",   # Tamil
                "tgt_lang": "en"    # English (romanized)
            },
            headers={"Authorization": f"Bearer {VAK_API_KEY}"},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json().get("result", text).lower()
        else:
            return text.lower()
            
    except requests.Timeout:
        print("⚠️ Shunya Vak timeout. Using fallback.")
        return text.lower()
    except Exception as e:
        print(f"⚠️ Tamil NLP error: {e}")
        return text.lower()


def parse_intent(text: str) -> Dict:
    """
    Detect what the passenger wants from their message.
    
    Intents:
    - 'eta'    → When will bus come?
    - 'seats'  → Are seats available?
    - 'status' → Is bus running today?
    
    Handles both Tamil script and Tanglish (English letters, Tamil words).
    """
    # Convert to English letters for easier matching
    english_text = transliterate_tamil(text).lower()
    
    # ── ETA Intent ───────────────────────────
    eta_keywords = [
        "bus", "eppo", "varum", "vandhucha",  # When will bus come
        "time", "when", "eta", "yarku",
        "yellai", "neram"
    ]
    
    # ── Seats Intent ─────────────────────────
    seat_keywords = [
        "seat", "iruppidam", "full",
        "place", "space", "available"
    ]
    
    # ── Status Intent ─────────────────────────
    status_keywords = [
        "running", "cancelled", "today",
        "iruka", "ille", "status", "nalaikku"
    ]
    
    # Check each intent
    if any(word in english_text for word in seat_keywords):
        return {"intent": "seats", "raw_text": text}
    
    if any(word in english_text for word in status_keywords):
        return {"intent": "status", "raw_text": text}
    
    # Default to ETA (most common query)
    return {"intent": "eta", "raw_text": text}


def extract_route_from_text(text: str) -> str:
    """
    Try to find a route number mentioned in message.
    Example: "47C bus eppo varum" → returns "47C"
    """
    import re
    # Look for patterns like 47C, 15, 100A, etc.
    pattern = r'\b(\d+[A-Z]?)\b'
    matches = re.findall(pattern, text.upper())
    
    if matches:
        return matches[0]
    return None