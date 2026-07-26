"""
kb_store.py
------------
The "knowledge base" the business trains its agent on (FR-2, FR-9 from the
business requirements doc): a list of question/answer entries the business
can add, edit, and delete without any ML knowledge.

Retrieval uses TF-IDF + cosine similarity (scikit-learn) — a lightweight,
fully offline alternative to embedding-based RAG. No model download, no API
key, works instantly. Good enough for a small business FAQ-sized knowledge
base; swap in a proper embedding model or a hosted service for production
scale.
"""

import json
import uuid
from pathlib import Path
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
KB_PATH = STORAGE_DIR / "kb.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_KB = [
    {"question": "What are your opening hours?",
     "answer": "We're open Monday to Friday 6am to 10pm, and weekends 8am to 8pm.",
     "category": "Hours"},
    {"question": "Do you offer day passes?",
     "answer": "Yes, a day pass is $15 and gives you full access to the gym floor and group classes that day.",
     "category": "Pricing"},
    {"question": "What membership plans do you have?",
     "answer": "We offer a monthly plan at $49/month with no contract, and an annual plan at $470/year which works out cheaper per month.",
     "category": "Pricing"},
    {"question": "Is there a pool?",
     "answer": "Yes, we have a 25-meter indoor pool open during all staffed hours.",
     "category": "Facilities"},
    {"question": "Can I freeze my membership?",
     "answer": "Yes, you can freeze your membership for up to 3 months per year at no extra cost — just let the front desk know at least 5 days in advance.",
     "category": "Policies"},
    {"question": "What classes do you offer on Saturday mornings?",
     "answer": "Saturday mornings we run a 7am spin class and an 8:30am beginner yoga class, both in Studio 2.",
     "category": "Classes"},
]


def _load() -> list:
    if KB_PATH.exists():
        return json.loads(KB_PATH.read_text())
    _save([{**e, "id": str(uuid.uuid4())[:8], "source_type": "manual"} for e in DEFAULT_KB])
    return _load()


def _save(entries: list) -> None:
    KB_PATH.write_text(json.dumps(entries, indent=2))


class KnowledgeBase:
    def __init__(self):
        self._entries = _load()
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None
        self._rebuild_index()

    def _rebuild_index(self):
        if not self._entries:
            self._vectorizer = None
            self._matrix = None
            return
        corpus = [f"{e['question']} {e['answer']}" for e in self._entries]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(corpus)

    def list_all(self) -> list:
        return self._entries

    def add(self, question: str, answer: str, category: str = "General") -> dict:
        entry = {
            "id": str(uuid.uuid4())[:8], "question": question, "answer": answer,
            "category": category, "source_type": "manual",
        }
        self._entries.append(entry)
        _save(self._entries)
        self._rebuild_index()
        return entry

    def add_document_chunks(self, filename: str, chunks: list) -> list:
        """
        Adds each chunk of an uploaded document as its own searchable entry.
        There's no natural "question" for a document chunk, so the chunk
        content itself is used for both — TF-IDF search still works fine
        since it matches on the combined text either way.
        """
        added = []
        for i, chunk in enumerate(chunks):
            entry = {
                "id": str(uuid.uuid4())[:8],
                "question": f"{filename} (part {i + 1})",
                "answer": chunk,
                "category": filename,
                "source_type": "document",
            }
            self._entries.append(entry)
            added.append(entry)
        _save(self._entries)
        self._rebuild_index()
        return added

    def delete_by_category(self, category: str) -> int:
        """Removes every chunk belonging to one uploaded document."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e["category"] != category]
        removed = before - len(self._entries)
        if removed:
            _save(self._entries)
            self._rebuild_index()
        return removed

    def update(self, entry_id: str, question: str, answer: str, category: str) -> Optional[dict]:
        for e in self._entries:
            if e["id"] == entry_id:
                e.update(question=question, answer=answer, category=category)
                _save(self._entries)
                self._rebuild_index()
                return e
        return None

    def delete(self, entry_id: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e["id"] != entry_id]
        if len(self._entries) == before:
            return False
        _save(self._entries)
        self._rebuild_index()
        return True

    def search(self, query: str, top_k: int = 1):
        """
        Returns up to top_k matches as (entry, score), best first.
        score is cosine similarity in [0, 1]; low scores mean "no good match".
        """
        if not self._entries or self._vectorizer is None:
            return []
        query_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(zip(self._entries, sims), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


_kb_singleton: Optional[KnowledgeBase] = None


def get_kb() -> KnowledgeBase:
    global _kb_singleton
    if _kb_singleton is None:
        _kb_singleton = KnowledgeBase()
    return _kb_singleton
