# services/voice_generator.py
# Generate Tamil voice audio using Google Text-to-Speech (gTTS)

import os
from gtts import gTTS
from pathlib import Path

# Directory to save audio files
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)  # Create if doesn't exist


async def generate_eta_audio(tamil_text: str, filename_prefix: str) -> str:
    """
    Convert Tamil text to MP3 audio file.
    
    Args:
        tamil_text: Text in Tamil (Tamil script or Tanglish)
        filename_prefix: Used to name the file uniquely
        
    Returns:
        Path to generated MP3 file
        
    Example:
        Input:  "Ungal 47C bus 12 nimalathil varum. 32 iruppidam ullo."
        Output: "audio/eta_+919876543210.mp3"
    """
    try:
        # Sanitize filename (remove special characters)
        safe_name = filename_prefix.replace("+", "").replace(" ", "_")
        audio_path = str(AUDIO_DIR / f"eta_{safe_name}.mp3")
        
        # Create gTTS object
        # lang='ta' = Tamil
        tts = gTTS(
            text=tamil_text,
            lang="ta",          # Tamil language
            slow=False          # Normal speed
        )
        
        # Save to file
        tts.save(audio_path)
        
        print(f"✅ Audio generated: {audio_path}")
        return audio_path
        
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        # Return a default audio path (you can pre-record a fallback)
        return "audio/default_error.mp3"


def cleanup_old_audio():
    """Delete audio files older than 1 hour to save disk space"""
    import time
    
    current_time = time.time()
    for audio_file in AUDIO_DIR.glob("*.mp3"):
        file_age = current_time - audio_file.stat().st_mtime
        if file_age > 3600:  # 1 hour = 3600 seconds
            audio_file.unlink()
            print(f"🗑️ Deleted old audio: {audio_file}") 