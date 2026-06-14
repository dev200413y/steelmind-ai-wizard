"""
OmniSense AI Wizard — Voice Utilities
Speech-to-Text: OpenAI Whisper (local, free, multilingual)
Text-to-Speech: gTTS (Google TTS, free, 30+ languages)
Supports 8 languages: Hindi, Odia, Bengali, Santali, English, Dutch, Welsh, Thai
"""

import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Language code mapping for gTTS
GTTS_LANG_MAP = {
    "hi": "hi",    # Hindi
    "or": "or",    # Odia  
    "bn": "bn",    # Bengali
    "en": "en",    # English
    "nl": "nl",    # Dutch
    "cy": "cy",    # Welsh
    "th": "th",    # Thai
    "sat": "en",   # Santali — fallback to English (gTTS doesn't support Santali)
}

# Whisper model — loaded once as singleton
_whisper_model = None

def _get_whisper():
    """Lazy load Whisper model (base for speed, use large-v3 for accuracy)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            model_size = os.getenv("WHISPER_MODEL", "base")
            logger.info(f"Loading Whisper model: {model_size}")
            _whisper_model = whisper.load_model(model_size)
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error("openai-whisper not installed. Run: pip install openai-whisper")
            raise
    return _whisper_model

def speech_to_text(audio_path: str) -> dict:
    """
    Transcribe audio file to text using Groq's lightning fast Whisper API (if available),
    falling back to local Whisper.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            import requests
            logger.info("🎙️ Transcribing with Groq Whisper API (Instant)")
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {groq_api_key}"}
            
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_path), audio_file, "audio/webm"),
                    "model": (None, "whisper-large-v3"),
                    "response_format": (None, "verbose_json"),
                }
                response = requests.post(url, headers=headers, files=files, timeout=15)
                
            if response.status_code == 200:
                data = response.json()
                return {
                    "text": data.get("text", "").strip(),
                    "language": data.get("language", "en"),
                    "confidence": 0.95
                }
            else:
                logger.warning(f"Groq API failed ({response.status_code}). Falling back to local.")
        except Exception as e:
            logger.error(f"Groq API Error: {e}. Falling back to local.")

    # Fallback to local Whisper
    try:
        model = _get_whisper()
        result = model.transcribe(
            audio_path,
            task="transcribe",
            fp16=False
        )
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "en"),
            "confidence": 0.9
        }
    except Exception as e:
        logger.error(f"Local Whisper failed: {e}")
        return {"text": "", "language": "en", "confidence": 0.0, "error": str(e)}

def text_to_speech(text: str, language: str = "en") -> str:
    """
    Convert text to speech using gTTS.
    
    Args:
        text: Text to speak (max 500 chars for speed)
        language: ISO 639-1 language code
        
    Returns:
        str: Path to generated MP3 file
    """
    try:
        from gtts import gTTS
        
        lang = GTTS_LANG_MAP.get(language, "en")
        
        # Truncate to 500 chars for speed — enough for diagnosis summary
        speak_text = text[:500] if len(text) > 500 else text
        
        # Ensure output directory exists
        out_dir = Path("uploads/audio_responses")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        tts = gTTS(text=speak_text, lang=lang, slow=False)
        
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=".mp3",
            dir=str(out_dir)
        )
        tts.save(tmp_file.name)
        
        logger.info(f"TTS generated: lang={lang}, file={tmp_file.name}")
        return tmp_file.name
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise

def generate_diagnosis_audio(diagnosis: dict, language: str = "en") -> str:
    """
    Generate spoken summary of diagnosis for engineer.
    Extracts the most important information for voice playback.
    
    Args:
        diagnosis: Diagnosis dict from DiagnosticAgent
        language: Response language code
        
    Returns:
        str: Path to MP3 file
    """
    fault = diagnosis.get("fault_identified", "Fault analysis complete")
    confidence = diagnosis.get("confidence", 0.0)
    first_action = diagnosis.get("repair_steps", [""])[0] if diagnosis.get("repair_steps") else ""
    immediate = diagnosis.get("immediate_actions", [""])[0] if diagnosis.get("immediate_actions") else ""
    shutdown = diagnosis.get("shutdown_required", False)
    
    # Build concise voice summary
    parts = [f"Diagnosis complete. {fault}."]
    
    if confidence > 0.7:
        parts.append(f"Confidence: {confidence:.0%}.")
    
    if shutdown:
        parts.append("WARNING: Immediate equipment shutdown required.")
    
    if immediate:
        parts.append(f"Immediate action: {immediate}")
    elif first_action:
        parts.append(f"First step: {first_action}")
    
    voice_text = " ".join(parts)
    return text_to_speech(voice_text, language)

def detect_language(text: str) -> str:
    """
    Heuristically detect the language of the provided text based on Unicode blocks.
    Supports Hindi (hi), Bengali (bn), Odia (or), Thai (th), Dutch (nl), and English (en).
    """
    import re
    if not text:
        return "en"
    
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"  # Devanagari (Hindi)
    if re.search(r'[\u0980-\u09FF]', text):
        return "bn"  # Bengali
    if re.search(r'[\u0B00-\u0B7F]', text):
        return "or"  # Odia
    if re.search(r'[\u0E00-\u0E7F]', text):
        return "th"  # Thai
    if re.search(r'\b(de|het|een|en|van|in|is|dat|op|te|zijn|voor|met|die|niet)\b', text.lower()):
        return "nl"  # Dutch heuristics
        
    return "en"  # Default to English

