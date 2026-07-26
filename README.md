FrontDesk — a local AI phone-agent builder

A working local implementation of a business requirements document: a business (using a gym, "Riverside Fitness," as the running example) trains an AI agent on its own knowledge base, then that agent handles simulated inbound calls — answering questions from uploaded documents or manual entries, booking classes, escalating sensitive topics to a human, and speaking in a choice of English, Hindi, or Gujarati voices — all runnable and testable entirely on your own machine.

What this maps to (business requirements)
Requirement	Where it lives
Answer calls automatically	Test Agent view simulates an inbound call
Business-trained knowledge base, editable by non-technical staff	Knowledge Base view — add Q&A manually, or upload a PDF/Word/text document
Answer natural spoken or typed questions from the knowledge base	agent_engine.py retrieves the best-matching entry via TF-IDF similarity
Check availability and book in real time	booking.py — a mock calendar with booking-intent detection
Escalate sensitive topics to a human	Keyword-based escalation check, always takes priority over KB answers
Log every call for staff review	Call Logs view — full transcript, resolved/escalated status
Consistent, choosable agent voice	Settings → Agent voice — 9 voices across English, Hindi, Gujarati
Support the languages customers speak	Agent replies are translated to match the selected voice's language
Tech stack
Backend: FastAPI
Knowledge base retrieval: TF-IDF + cosine similarity (scikit-learn) — fully offline, no API key
Document upload: PDF (pypdf), Word (python-docx), plain text/markdown — chunked and indexed automatically
Speech-to-text (customer's spoken turns): OpenAI's open-source Whisper, running locally
Text-to-speech (agent's replies): 9 voices across English, Hindi, and Gujarati — see "Voices and languages" below
Translation: free Google translation (deep-translator) — translates the agent's English answer into Hindi/Gujarati to match the selected voice (requires internet; see limitations below)
Frontend: a single-page dashboard (vanilla HTML/CSS/JS) — sidebar navigation, a live call simulator, a knowledge base manager, call logs, and a settings panel
Project structure
frontdesk/
├── backend/
│   ├── main.py             # FastAPI app + all routes
│   ├── agent_engine.py      # escalation check -> booking check -> KB retrieval -> fallback
│   ├── kb_store.py           # knowledge base storage + TF-IDF search
│   ├── doc_processor.py       # PDF/Word/text extraction + chunking for uploads
│   ├── booking.py               # mock calendar
│   ├── calls_store.py            # call transcript logging
│   ├── settings_store.py          # agent configuration (name, greeting, voice, keywords)
│   ├── tts_engine.py               # speech generation (9 voices, 3 languages)
│   ├── stt_engine.py                # speech transcription (Whisper)
│   ├── translate.py                  # Hindi/Gujarati reply translation
│   └── requirements.txt
├── frontend/
│   └── index.html                     # dashboard UI
├── storage/
│   ├── kb.json                          # knowledge base (auto-created with sample gym FAQs)
│   ├── settings.json                     # agent config (auto-created)
│   ├── calls.json                         # call logs (auto-created)
│   └── audio/                              # generated speech output
└── README.md
Requirements
Python 3.10, 3.11, or 3.13 (see the Whisper note under Troubleshooting if on 3.13)
ffmpeg installed and on PATH — required for Whisper (decoding recorded voice clips) and for converting Gujarati/Hindi Google voices to .wav:
macOS: brew install ffmpeg
Linux: sudo apt install ffmpeg
Windows: install via ffmpeg.org and add to PATH
Linux only: install espeak as a fallback voice engine: sudo apt install espeak (macOS uses its built-in say command — no extra install needed for English/Hindi voices)
A browser with MediaRecorder support and a microphone, if you want to test by voice (typing always works, no mic required)
No GPU required — everything is deliberately lightweight so it runs fast on a laptop CPU
Internet connection needed only for: Gujarati/Google-Hindi voices, and Hindi/Gujarati reply translation. Everything else works fully offline.
Setup
bash
cd frontdesk/backend

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

uvicorn main:app --reload --port 8000

Open http://localhost:8000.

Using it
Knowledge Base: pre-loaded with sample gym FAQs (hours, pricing, pool, classes, policies).
Click "+ Add entry" to add a manual question/answer pair.
Click "Upload document" to add a PDF, Word doc, or text/markdown file — it's automatically split into searchable chunks. Delete a whole uploaded document (all its chunks) with one click from its card.
Test Agent: click "Start test call". The agent speaks its greeting aloud. Reply by typing or by clicking the mic and speaking. Try:
A normal FAQ ("What are your hours?") → answered from the knowledge base
A booking request ("Can I book the Saturday spin class?") → checks the mock calendar and confirms
A sensitive topic ("I want to file a complaint") → instantly escalated
Something off-topic → no confident match → falls back and escalates
Call Logs: every test call is saved with its full transcript and a Resolved/Escalated status.
Settings: business name, agent name, greeting, fallback message, escalation keywords, and Agent voice — pick from 9 voices, click "Preview voice" to hear a sample before saving.
Voices and languages

Go to Settings → Agent voice to pick from 9 voices:

Voice	Language	Gender	Engine	Needs internet?
Samantha	English (US)	Female	macOS say	No
Alex	English (US)	Male	macOS say	No
Daniel	English (UK)	Male	macOS say	No
Karen	English (Australia)	Female	macOS say	No
Moira	English (Ireland)	Female	macOS say	No
Veena	English (India accent)	Female	macOS say	No
Lekha	Hindi	Female	macOS say	No
Hindi (Google)	Hindi	—	gTTS	Yes
Gujarati (Google)	Gujarati	—	gTTS	Yes

If a say voice isn't installed on your Mac, Settings marks it "(not installed)" — add it via System Settings → Accessibility → Spoken Content → System Voice → Manage Voices, then refresh. On Linux, macOS-only voices fall back to espeak in the closest matching language automatically.

Hindi/Gujarati replies: picking a Hindi or Gujarati voice now translates the agent's English answer into that language (via free Google translation) before it's spoken and before it's shown in the chat — so the agent actually responds in that language, not just with an accent.

Known limitations, honestly stated:

Free machine translation is noticeably less accurate than a native speaker or a paid translation API — expect rough edges, especially with business-specific terms ("membership," "spin class"). For your most common questions, consider writing native Hindi/Gujarati answers by hand instead of relying on live translation.
The customer's question is transcribed by Whisper in whatever language they speak, but the knowledge base search still matches against English text — so a question asked in Hindi/Gujarati may not match a KB entry well, even though the answer comes back translated correctly.
If there's no internet connection, Hindi/Gujarati voices and translation silently fall back to English rather than erroring out.
Extending this project
Idea	How
Better answer quality	Replace "return the top KB match verbatim" in agent_engine.py with an LLM call, passing retrieved KB entries as context (real RAG)
Native Hindi/Gujarati answers	Add a language field to KB entries and write hand-translated versions of your top FAQs, skipping live translation for those
Real phone calls	Connect the /api/calls/* endpoints to a Twilio number instead of the browser simulator
Production-grade voice	Swap tts_engine.py's say/gTTS voices for a real ElevenLabs API call
Bilingual search	Translate the customer's transcribed question into English before running it through the knowledge base search
Real calendar	Swap booking.py for a Google Calendar or Calendly API integration
CRM logging	Push each finished call from calls_store.py into a real CRM via webhook
Troubleshooting

Issues actually hit while building/running this, and their fixes:

ModuleNotFoundError: No module named 'pkg_resources' when installing Whisper (Python 3.13) Newer setuptools removed pkg_resources, which Whisper's old installer still expects.

bash
pip install "setuptools<81"
pip install --no-build-isolation openai-whisper

uvicorn: command not found or it loads the wrong Python packages Your global Python may be shadowing your virtual environment. Always run it as a module instead:

bash
python -m uvicorn main:app --reload --port 8000

Voice replies never happen / server hangs on pyttsx3 pyttsx3 has real compatibility bugs with newer pyobjc on macOS. This project no longer uses it — tts_engine.py uses macOS's built-in say command and gTTS instead. If you're on an old copy of this project that still imports pyttsx3, update to the current tts_engine.py.

Mic recording gives a 500 Internal Server Error / CORS-looking error in the browser console This usually means ffmpeg isn't installed — Whisper needs it to decode the browser's recorded audio.

bash
brew install ffmpeg      # macOS
sudo apt install ffmpeg  # Linux

Homebrew refuses to install anything, mentioning "untrusted tap" An old tap (e.g. mongodb/brew) is blocking trust checks for everything. Trust it rather than removing it if you still use it:

bash
brew trust mongodb/brew

Mic button does nothing in Safari Safari handles mic permissions separately from Chrome. Go to Safari → Settings → Websites → Microphone, set localhost to Allow, and check System Settings → Privacy & Security → Microphone has Safari enabled.

Made a code change but the app looks unchanged in the browser This is almost always the browser cache, not the code. Open DevTools (Cmd+Option+I), right-click the reload button, choose "Empty Cache and Hard Reload". To confirm it's caching and not a missed file update, check what the server is actually sending:

bash
curl -s http://localhost:8000/ | grep -c "some_unique_string_from_your_edit"

If that returns a number greater than 0, the server is fine and it's purely a browser cache issue.

Port 8000 already in use

bash
kill -9 $(lsof -t -i:8000) 2>/dev/null

Run this before starting the server again.

Notes on the design choices

The knowledge base uses TF-IDF instead of a hosted embedding model on purpose — it means this project runs entirely offline (aside from the optional Hindi/Gujarati voice and translation features) with zero required API keys and starts up instantly. It's a real limitation compared to what a production RAG system or ElevenLabs' own knowledge base can do (semantic understanding vs. keyword/term overlap) — worth keeping in mind as you compare this learning prototype to a real product.

