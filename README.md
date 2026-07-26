# FrontDesk

A local AI phone-agent prototype for small businesses. It answers customer questions from a knowledge base (typed manually or uploaded as PDF/Word/text documents), checks a mock calendar to book appointments, escalates sensitive topics to a human, and replies by voice in English, Hindi, or Gujarati — all tested through a browser-based call simulator.

**Status:** Proof of concept. Runs fully offline, except Hindi/Gujarati voice and translation which need internet. Not yet connected to a real phone line.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Knowledge base search:** TF-IDF + cosine similarity (scikit-learn)
- **Speech-to-text:** OpenAI Whisper
- **Text-to-speech:** macOS `say` (offline) + gTTS (Hindi/Gujarati)
- **Translation:** Google Translate via `deep-translator`
- **Document parsing:** pypdf, python-docx
- **Frontend:** Vanilla HTML/CSS/JS

## Features

- Manual Q&A entries or document upload to build the knowledge base
- Voice or text-based test calls
- Automatic escalation for sensitive topics (complaints, injuries, disputes)
- Mock class booking with live availability
- Full call transcript logging (resolved/escalated status)
- 9 selectable voices across English, Hindi, and Gujarati

## Setup

```bash
cd frontdesk/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000.

## Requirements

- Python 3.10+
- `ffmpeg` installed (for speech transcription and Hindi/Gujarati voices)
- macOS: no extra setup for English/Hindi voices (uses built-in `say`)
- Linux: install `espeak` as a fallback voice engine
