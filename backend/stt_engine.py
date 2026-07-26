"""
stt_engine.py
--------------
Transcribes the customer's spoken turn using OpenAI's open-source Whisper
model (runs locally, no API key). Lazily loaded once and reused.
"""

from typing import Optional

_model = None


def _get_model():
    global _model
    if _model is None:
        import whisper
        # "base" is small and fast enough for CPU; use "small"/"medium" for
        # better accuracy if you have a GPU.
        _model = whisper.load_model("base")
    return _model


def transcribe(file_path: str) -> str:
    model = _get_model()
    result = model.transcribe(file_path)
    return result["text"].strip()
