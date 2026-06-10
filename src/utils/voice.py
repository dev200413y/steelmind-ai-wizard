"""
SteelMind AI Wizard — Voice Utilities
======================================
Handles speech-to-text (Whisper), text-to-speech (gTTS), and language detection.
"""

import os
import logging
from pathlib import Path
from gtts import gTTS
import whisper

logger = logging.getLogger(__name__)

# Load whisper model lazily to avoid long startup times if not used immediately
_whisper_model = None

def get_whisper_model():
    """Load Whisper model singleton."""
    global _whisper_model
    if _whisper_model is None:
        logger.info("🎙️ Loading Whisper base model...")
        _whisper_model = whisper.load_model("base")
    return _whisper_model

def detect_language(text: str) -> str:
    """
    Simple language detection from text.
    In a real app, you might use langdetect or fasttext.
    For this prototype, Whisper detects it during STT.
    If direct text input, default to 'en' or do a basic heuristic.
    """
    # Simple heuristic for demonstration purposes
    # Whisper's language detection is robust, so this is mostly a fallback.
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "hi" # Hindi
    if any("\u0980" <= c <= "\u09FF" for c in text):
        return "bn" # Bengali
    if any("\u0B00" <= c <= "\u0B7F" for c in text):
        return "or" # Odia
    
    return "en"

def transcribe_audio(audio_path: str) -> tuple[str, str]:
    """
    Transcribe audio file using OpenAI Whisper.
    Returns (transcribed_text, language_code).
    """
    logger.info(f"🎙️ Transcribing audio: {audio_path}")
    try:
        model = get_whisper_model()
        result = model.transcribe(audio_path)
        
        text = result["text"].strip()
        language = result.get("language", "en")
        
        logger.info(f"✅ Transcribed ({language}): {text[:50]}...")
        return text, language
        
    except Exception as e:
        logger.error(f"❌ Whisper transcription failed: {str(e)}")
        return "", "en"

def text_to_speech(text: str, language: str = "en") -> str:
    """
    Convert text to speech using gTTS and save to a file.
    Returns the path to the saved audio file.
    """
    logger.info(f"🔊 Generating TTS audio in {language}")
    try:
        # Create output directory
        out_dir = Path("uploads/audio_responses")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Mapping from whisper language codes to gtts language codes if needed
        # Mostly they are the same (en, hi, bn). Odia (or) might not be fully supported by gTTS depending on version.
        gtts_lang = language if language in ['en', 'hi', 'bn', 'nl', 'th', 'cy'] else 'en'
        
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        output_path = out_dir / f"response_{os.urandom(4).hex()}.mp3"
        tts.save(str(output_path))
        
        logger.info(f"✅ TTS saved: {output_path}")
        return str(output_path.absolute())
        
    except Exception as e:
        logger.error(f"❌ TTS generation failed: {str(e)}")
        return ""
