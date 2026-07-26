"""
tts_engine.py
--------------
Generates the agent's spoken replies, with a choice of voices across
English, Hindi, and Gujarati (FR-7 / FR-8 from the business requirements).

Two engines are used:
  - "say": macOS's built-in offline voice engine. Covers several English
    voices (male + female) and one native Hindi voice (Lekha). Free,
    instant, no internet required — but macOS-only, and some voices may
    need to be downloaded once via System Settings -> Accessibility ->
    Spoken Content -> System Voice -> Manage Voices.
  - "gtts": Google's free web-based text-to-speech. Used for Gujarati,
    since macOS has no built-in Gujarati voice, and as a Hindi
    alternative. Requires an internet connection (this is the one part
    of the project that isn't fully offline) and the `gtts` package.

On Linux, "say" voices fall back to espeak with the closest matching
language, since macOS's `say` isn't available there.
"""

import platform
import subprocess
import uuid
from pathlib import Path

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
AUDIO_DIR = STORAGE_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

IS_MAC = platform.system() == "Darwin"

VOICE_CATALOG = [
    {"id": "en_samantha", "label": "Samantha - English (US), female", "language": "English",
     "engine": "say", "say_voice": "Samantha"},
    {"id": "en_alex", "label": "Alex - English (US), male", "language": "English",
     "engine": "say", "say_voice": "Alex"},
    {"id": "en_daniel", "label": "Daniel - English (UK), male", "language": "English",
     "engine": "say", "say_voice": "Daniel"},
    {"id": "en_karen", "label": "Karen - English (Australia), female", "language": "English",
     "engine": "say", "say_voice": "Karen"},
    {"id": "en_moira", "label": "Moira - English (Ireland), female", "language": "English",
     "engine": "say", "say_voice": "Moira"},
    {"id": "en_veena", "label": "Veena - English (India accent), female", "language": "English",
     "engine": "say", "say_voice": "Veena"},
    {"id": "hi_lekha", "label": "Lekha - Hindi, female (offline)", "language": "Hindi",
     "engine": "say", "say_voice": "Lekha"},
    {"id": "hi_gtts", "label": "Hindi - Google voice (online)", "language": "Hindi",
     "engine": "gtts", "gtts_lang": "hi"},
    {"id": "gu_gtts", "label": "Gujarati - Google voice (online)", "language": "Gujarati",
     "engine": "gtts", "gtts_lang": "gu"},
]

DEFAULT_VOICE_ID = "en_samantha"

_LINUX_ESPEAK_LANG = {"English": "en", "Hindi": "hi", "Gujarati": "gu"}


def get_voice(voice_id: str) -> dict:
    return next((v for v in VOICE_CATALOG if v["id"] == voice_id), VOICE_CATALOG[0])


def list_installed_say_voices() -> set:
    """
    Returns the set of macOS `say` voice names actually installed on this
    machine, so the UI can flag catalog entries that need to be downloaded
    first (System Settings -> Accessibility -> Spoken Content -> Manage
    Voices) rather than just failing silently when picked.
    """
    if not IS_MAC:
        return set()
    try:
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True)
        return {line.split()[0] for line in result.stdout.splitlines() if line.strip()}
    except Exception:
        return set()


def synthesize(text: str, voice_id: str = DEFAULT_VOICE_ID) -> str:
    """
    Generates speech for `text` using the given voice_id and returns the
    path to the saved .wav file.
    """
    voice = get_voice(voice_id)
    output_path = AUDIO_DIR / f"{uuid.uuid4().hex[:12]}.wav"

    if voice["engine"] == "say":
        if IS_MAC:
            subprocess.run(
                ["say", "-v", voice["say_voice"], "-o", str(output_path), "--data-format=LEF32@22050", text],
                check=True,
            )
        else:
            # Linux: no `say` command -- fall back to espeak in the closest language.
            lang = _LINUX_ESPEAK_LANG.get(voice["language"], "en")
            subprocess.run(["espeak", "-v", lang, text, "-w", str(output_path)], check=True)

    elif voice["engine"] == "gtts":
        from gtts import gTTS
        mp3_path = output_path.with_suffix(".mp3")
        gTTS(text=text, lang=voice["gtts_lang"]).save(str(mp3_path))
        # Convert to .wav so every voice's output is served consistently.
        subprocess.run(["ffmpeg", "-y", "-i", str(mp3_path), str(output_path)],
                        check=True, capture_output=True)
        mp3_path.unlink(missing_ok=True)

    return str(output_path)
