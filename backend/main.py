"""
main.py — FrontDesk backend
-----------------------------
Run locally with:
    uvicorn main:app --reload --port 8000

Then open http://localhost:8000. Nothing here is deployed publicly.

This implements the business requirements document as a working local
prototype: a business's own knowledge base drives an agent that handles a
simulated customer call (by voice or typed text), checks for booking
intent against a mock calendar, escalates sensitive topics to "a human",
and logs every call for review.

Endpoints:
    GET/POST/PUT/DELETE /api/kb              knowledge base entries
    GET/POST            /api/settings        agent configuration
    GET                  /api/availability   mock class schedule
    POST /api/calls/start                    begin a simulated call
    POST /api/calls/{id}/turn                one customer turn (voice or text)
    POST /api/calls/{id}/end                 finalize a call
    GET  /api/calls                          call log list
    GET  /api/calls/{id}                     full transcript
    GET  /api/audio/{filename}               generated speech audio
"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent_engine
import booking
import calls_store
import doc_processor
import stt_engine
import translate
import tts_engine
from kb_store import get_kb
from settings_store import get_settings, save_settings
from tts_engine import AUDIO_DIR

app = FastAPI(title="FrontDesk (local prototype)", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local prototype only
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------- Knowledge base ----------------

class KBEntryIn(BaseModel):
    question: str
    answer: str
    category: str = "General"


@app.get("/api/kb")
def list_kb():
    return {"entries": get_kb().list_all()}


@app.post("/api/kb")
def add_kb(entry: KBEntryIn):
    return get_kb().add(entry.question, entry.answer, entry.category)


@app.put("/api/kb/{entry_id}")
def update_kb(entry_id: str, entry: KBEntryIn):
    updated = get_kb().update(entry_id, entry.question, entry.answer, entry.category)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry not found.")
    return updated


@app.delete("/api/kb/{entry_id}")
def delete_kb(entry_id: str):
    if not get_kb().delete(entry_id):
        raise HTTPException(status_code=404, detail="Entry not found.")
    return {"deleted": entry_id}


@app.post("/api/kb/upload")
async def upload_kb_document(document: UploadFile = File(...)):
    """
    Upload a PDF, Word doc, or text/markdown file. It's extracted, split
    into chunks, and each chunk is added as its own searchable knowledge
    base entry, grouped under the filename as its category.
    """
    filename = document.filename or "document"
    suffix = Path(filename).suffix.lower()
    if suffix not in doc_processor.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported: {', '.join(doc_processor.SUPPORTED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await document.read())
        tmp_path = tmp.name

    try:
        text = doc_processor.extract_text(tmp_path, filename)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Couldn't extract any text from that file.")
        chunks = doc_processor.chunk_text(text)
        added = get_kb().add_document_chunks(filename, chunks)
    finally:
        os.unlink(tmp_path)

    return {"filename": filename, "chunks_added": len(added)}


@app.delete("/api/kb/document/{filename}")
def delete_kb_document(filename: str):
    removed = get_kb().delete_by_category(filename)
    if not removed:
        raise HTTPException(status_code=404, detail="No chunks found for that document.")
    return {"filename": filename, "chunks_removed": removed}


# ---------------- Settings ----------------

@app.get("/api/settings")
def read_settings():
    return get_settings()


@app.post("/api/settings")
def write_settings(settings: dict):
    return save_settings(settings)


# ---------------- Booking / availability ----------------

@app.get("/api/availability")
def availability():
    return {"classes": booking.list_availability()}


# ---------------- Voices ----------------

@app.get("/api/voices")
def list_voices():
    installed = tts_engine.list_installed_say_voices()
    catalog = []
    for v in tts_engine.VOICE_CATALOG:
        entry = dict(v)
        if v["engine"] == "say":
            entry["available"] = v["say_voice"] in installed if installed else True
        else:
            entry["available"] = True  # gtts availability depends on internet, checked at call time
        catalog.append(entry)
    return {"voices": catalog}


@app.post("/api/voices/preview")
def preview_voice(voice_id: str = Form(...)):
    voice = tts_engine.get_voice(voice_id)
    sample_text = {
        "English": "Hi, this is a preview of my voice.",
        "Hindi": "नमस्ते, यह मेरी आवाज़ का एक नमूना है।",
        "Gujarati": "નમસ્તે, આ મારા અવાજનો નમૂનો છે.",
    }.get(voice["language"], "Hi, this is a preview of my voice.")
    try:
        audio_path = tts_engine.synthesize(sample_text, voice_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Couldn't generate that voice: {e}")
    return {"audio_url": f"/api/audio/{Path(audio_path).name}"}


# ---------------- Calls ----------------

@app.post("/api/calls/start")
def start_call():
    settings = get_settings()
    greeting = settings.get("greeting", "Thanks for calling, how can I help?")
    voice_id = settings.get("voice_id", tts_engine.DEFAULT_VOICE_ID)
    voice = tts_engine.get_voice(voice_id)

    spoken_greeting = translate.translate_if_needed(greeting, voice["language"])

    call = calls_store.create_call(spoken_greeting)
    audio_path = tts_engine.synthesize(spoken_greeting, voice_id)
    return {
        "call_id": call["id"],
        "greeting_text": spoken_greeting,
        "audio_url": f"/api/audio/{Path(audio_path).name}",
    }


@app.post("/api/calls/{call_id}/turn")
async def call_turn(
    call_id: str,
    text: str = Form(None),
    audio: UploadFile = File(None),
):
    call = calls_store.get_call(call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found.")

    # Accept either a typed message or a recorded voice clip for this turn.
    if audio is not None:
        suffix = Path(audio.filename or "turn.webm").suffix or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
        try:
            user_text = stt_engine.transcribe(tmp_path)
        finally:
            os.unlink(tmp_path)
    elif text:
        user_text = text.strip()
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'audio'.")

    if not user_text:
        raise HTTPException(status_code=400, detail="Could not understand that — try again.")

    calls_store.append_turn(call_id, "customer", user_text)

    result = agent_engine.handle_turn(user_text, get_kb())

    settings = get_settings()
    voice_id = settings.get("voice_id", tts_engine.DEFAULT_VOICE_ID)
    voice = tts_engine.get_voice(voice_id)
    spoken_reply = translate.translate_if_needed(result["reply"], voice["language"])

    calls_store.append_turn(
        call_id, "agent", spoken_reply,
        meta={"escalated": result["escalated"], "action": result["action"]},
    )

    audio_path = tts_engine.synthesize(spoken_reply, voice_id)

    return {
        "user_text": user_text,
        "agent_text": spoken_reply,
        "audio_url": f"/api/audio/{Path(audio_path).name}",
        "escalated": result["escalated"],
        "action": result["action"],
    }


@app.post("/api/calls/{call_id}/end")
def end_call(call_id: str):
    call = calls_store.end_call(call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found.")
    return call


@app.get("/api/calls")
def list_calls():
    return {"calls": calls_store.list_calls()}


@app.get("/api/calls/{call_id}")
def get_call(call_id: str):
    call = calls_store.get_call(call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found.")
    return call


@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    path = AUDIO_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(path, media_type="audio/wav")


# Serve the frontend directly from the backend.
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    