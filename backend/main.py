from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
try:
    from .rag_engine import initialize_rag_system, get_answer
    from .voice_processor import transcribe_audio, text_to_speech
except ImportError:
    from rag_engine import initialize_rag_system, get_answer
    from voice_processor import transcribe_audio, text_to_speech

app = FastAPI(title="Khadamat AI: Assistant Administratif Intelligent")

# Configuration CORS pour permettre à l'interface web de parler au backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines pour le développement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for file paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILES = [
    os.path.join(BASE_DIR, "morocco_admin_dataset.md"),
    os.path.join(BASE_DIR, "version arabe.md"),
    os.path.join(BASE_DIR, "version darija.md")
]

@app.get("/")
async def read_index():
    """Sert le fichier index.html à la racine."""
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.on_event("startup")
async def startup_event():
    """
    Initialize the RAG system on startup.
    Loads documents and creates vector store.
    """
    try:
        print("Initializing RAG system...")
        initialize_rag_system(DATA_FILES)
        print("Done.")
    except Exception as e:
        print(f"Failed to initialize RAG system: {e}")

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask-text/")
async def ask_text_endpoint(request: QuestionRequest):
    """
    Endpoint for text-based interaction.
    Input: JSON {"question": "Question text"}
    Output: JSON {"answer": "Answer text"}
    """
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="Empty question")
        
        answer = get_answer(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-audio/")
async def ask_audio_endpoint(file: UploadFile = File(...)):
    """
    Endpoint for audio-based interaction.
    Input: Audio file (WAV, MP3, etc.)
    Output: Audio file response (MP3)
    PROTOTYPE FLOW:
    1. Save uploaded audio to temp file.
    2. Transcribe using Whisper (STT).
    3. Query RAG system with transcribed text.
    4. Convert text answer using gTTS (TTS).
    5. Return audio file.
    """
    try:
        # 1. Save uploaded file
        temp_input = f"temp_{file.filename}"
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. STT
        transcription = transcribe_audio(temp_input)
        
        # Clean up input file
        os.remove(temp_input)
        
        if not transcription:
             raise HTTPException(status_code=400, detail="Could not transcribe audio.")

        # 3. RAG
        # We pass the transcription as the user question
        answer_text = get_answer(transcription)

        # 4. TTS
        output_audio_path = "response_audio.mp3"
        result_path = text_to_speech(answer_text, output_audio_path)
        
        if not result_path:
             raise HTTPException(status_code=500, detail="Could not generate audio response.")

        # 5. Return audio file
        return FileResponse(result_path, media_type="audio/mpeg", filename="response.mp3")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
