import os
import re
from gtts import gTTS
from elevenlabs.client import ElevenLabs

try:
    import speech_recognition as sr
except ImportError as e:
    sr = None
    import sys
    print(f"Warning: speech_recognition module not found ({e}). Google STT disabled.")
    print(f"Python Executable causing error: {sys.executable}")
except Exception as e:
    sr = None
    import sys
    print(f"Warning: speech_recognition failed to import ({e}). Google STT disabled.")
    print(f"Python Executable causing error: {sys.executable}")

# Initialize ElevenLabs client from environment variable.
API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()

# We initialize the client but handle potential import errors gracefully
try:
    client = ElevenLabs(api_key=API_KEY)
except Exception as e:
    print(f"Failed to initialize ElevenLabs client: {e}")
    client = None

def _fallback_stt_google(audio_file_path: str) -> str:
    """Fallback to Google Speech Recognition (Free) if ElevenLabs fails."""
    if sr is None:
        print("Google STT disabled: speech_recognition module missing.")
        return ""
        
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data = r.record(source)
            # Try Arabic first (Darija often transcribed as Arabic or mixed)
            try:
                text = r.recognize_google(audio_data, language="ar-MA")
                if text: return text
            except sr.UnknownValueError:
                pass # Try French
            
            # Try French
            try:
                text = r.recognize_google(audio_data, language="fr-FR")
                if text: return text
            except sr.UnknownValueError:
                pass
                
            return ""
    except Exception as e:
        print(f"Google STT Fallback failed: {e}")
        return ""

def _looks_wrong_language(text: str) -> bool:
    if not text or not text.strip():
        return True

    cleaned = text.strip()
    cjk_or_hangul = re.findall(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]", cleaned)
    latin_or_arabic = re.findall(r"[A-Za-zÀ-ÿ\u0600-\u06FF]", cleaned)

    # Strong signal that transcription drifted to unrelated East-Asian output.
    if len(cjk_or_hangul) >= 3 and len(cjk_or_hangul) > len(latin_or_arabic):
        return True

    return False

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes audio file to text using ElevenLabs Speech-to-Text (Scribe),
    with a fallback to Google Speech Recognition.
    """
    elevenlabs_result = ""
    
    # Try ElevenLabs first
    if client:
        try:
            if not os.path.exists(audio_file_path):
                print(f"File not found: {audio_file_path}")
                return ""
                
            # First pass: automatic language detection
            with open(audio_file_path, "rb") as audio_file:
                transcription = client.speech_to_text.convert(
                    file=audio_file,
                    model_id="scribe_v1",
                    tag_audio_events=False
                )

            elevenlabs_result = getattr(transcription, "text", "") or ""
            elevenlabs_result = elevenlabs_result.strip()

            # Retry with explicit French if transcription appears clearly wrong.
            if _looks_wrong_language(elevenlabs_result):
                print(f"ElevenLabs output suspect ('{elevenlabs_result}'), retrying with 'fr'...")
                with open(audio_file_path, "rb") as audio_file:
                    retry = client.speech_to_text.convert(
                        file=audio_file,
                        model_id="scribe_v1",
                        language_code="fr",
                        tag_audio_events=False
                    )
                retry_text = getattr(retry, "text", "") or ""
                retry_text = retry_text.strip()
                
                if not _looks_wrong_language(retry_text):
                    elevenlabs_result = retry_text
                # If both are bad, we might fallback to Google
                
        except Exception as e:
            print(f"Error in transcription (ElevenLabs): {e}")
            elevenlabs_result = ""

    # If ElevenLabs failed or produced empty/bad result, try Google Fallback
    if not elevenlabs_result or _looks_wrong_language(elevenlabs_result):
        # We try Google
        print("Falling back to Google Speech Recognition...")
        google_result = _fallback_stt_google(audio_file_path)
        if google_result:
            return google_result
            
        # If Google also fails but we had a 'bad' ElevenLabs result, return that at least?
        # Or return empty so user is asked to repeat.
        if elevenlabs_result and len(elevenlabs_result) > 5:
             # Just return the possibly bad result rather than failing completely
             return elevenlabs_result
             
        return ""

    return elevenlabs_result

def text_to_speech(text: str, output_path: str = "output_audio.mp3") -> str:
    """
    Converts text to speech using ElevenLabs (Multilingual v2).
    Falls back to gTTS if ElevenLabs fails or is not available.
    """
    # Try ElevenLabs first
    if client:
        try:
            # Use a multilingual model for Arabic/French support
            model_id = "eleven_multilingual_v2"
            # Voice ID: "Rachel" (21m00Tcm4TlvDq8ikWAM)
            voice_id = "21m00Tcm4TlvDq8ikWAM" 
            
            # Generate audio
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id
            )
            
            # Save the audio to file manually to be safe
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
            
            return output_path
        except Exception as e:
            print(f"Error in TTS (ElevenLabs): {e}. Falling back to gTTS.")
    else:
        print("ElevenLabs client not initialized. Falling back to gTTS.")

    # Fallback to gTTS
    try:
        # Detect language logic
        lang = 'fr'
        # Simple heuristic: if more Arabic chars than Latin, use 'ar'
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        latin_chars = len(re.findall(r"[A-Za-z]", text))
        if arabic_chars > latin_chars:
            lang = 'ar'
            
        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error in TTS (gTTS): {e}")
        return None