"""Notes-to-Study-Kit: turn a photo of notes into a summary, flashcards and a quiz.
 
Backend: Flask. Model: Gemma 4 (open weights) served through the Gemini API.
"""
 
import json
import os
import re
import time
from collections import defaultdict, deque
 
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types
 
load_dotenv()
 
# Gemma 4 model IDs available on the Gemini API:
#   gemma-4-26b-a4b-it (smaller active params, faster)
#   gemma-4-31b-it     (larger, higher quality)
MODEL_LABELS = {
    "gemma-4-26b-a4b-it": "Fast (Gemma 4 26B A4B)",
    "gemma-4-31b-it": "Best quality (Gemma 4 31B)",
}
MODEL = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
if MODEL not in MODEL_LABELS:  # env var typo or unknown model: fall back safely
    MODEL = "gemma-4-26b-a4b-it"
MAX_IMAGES = 4
MAX_IMAGE_BYTES = 6 * 1024 * 1024
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
LANGUAGES = {"English", "Hindi", "Marathi"}
 
# Very small in-memory rate limit so a public demo can't burn the API key.
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "6"))
_hits = defaultdict(deque)
 
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGES * MAX_IMAGE_BYTES + 1024 * 1024
 
_client = None
 
 
def get_client():
    """Create the Gemini API client lazily so the app boots without a key."""
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=key)
    return _client
 
 
PROMPT = """You are a study assistant. The attached image(s) are a student's notes
or a textbook page (possibly handwritten, possibly messy).
 
1. Read everything you can see.
2. Build a study kit ONLY from what the notes actually say. Do not invent facts.
   If something is unreadable, skip it.
3. Write every text field in {language}.
 
Return ONLY one JSON object, no markdown fences, no commentary, with exactly this shape:
{{
  "title": "short topic title",
  "summary": ["5-8 concise bullet points"],
  "key_terms": [{{"term": "...", "definition": "..."}}],
  "flashcards": [{{"q": "...", "a": "..."}}],
  "quiz": [{{
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "answer_index": 0,
    "explanation": "one sentence on why this is correct"
  }}]
}}
 
Produce {n_cards} flashcards and {n_quiz} quiz questions. Each quiz question has exactly
4 options, exactly one correct, and answer_index is the 0-based index of the correct option.
"""
 
 
def extract_json(text):
    """Pull a JSON object out of model text, tolerating fences or extra prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object in model output")
    return json.loads(text[start : end + 1])
 
 
def clean_kit(kit):
    """Validate and normalise the model output so the frontend can trust it."""
    out = {
        "title": str(kit.get("title") or "Study kit")[:120],
        "summary": [str(s) for s in kit.get("summary", []) if str(s).strip()],
        "key_terms": [],
        "flashcards": [],
        "quiz": [],
    }
    for t in kit.get("key_terms", []):
        if isinstance(t, dict) and t.get("term") and t.get("definition"):
            out["key_terms"].append(
                {"term": str(t["term"]), "definition": str(t["definition"])}
            )
    for c in kit.get("flashcards", []):
        if isinstance(c, dict) and c.get("q") and c.get("a"):
            out["flashcards"].append({"q": str(c["q"]), "a": str(c["a"])})
    for q in kit.get("quiz", []):
        if not isinstance(q, dict):
            continue
        opts = q.get("options")
        idx = q.get("answer_index")
        if (
            q.get("question")
            and isinstance(opts, list)
            and len(opts) == 4
            and isinstance(idx, int)
            and 0 <= idx < 4
        ):
            out["quiz"].append(
                {
                    "question": str(q["question"]),
                    "options": [str(o) for o in opts],
                    "answer_index": idx,
                    "explanation": str(q.get("explanation", "")),
                }
            )
    return out
 
 
def rate_limited(ip):
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return True
    q.append(now)
    return False
 
 
def clamp(value, lo, hi, default):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default
 
 
@app.get("/")
def index():
    return render_template("index.html", model=MODEL, models=MODEL_LABELS)
 
 
@app.get("/health")
def health():
    return jsonify(status="ok", model=MODEL)
 
 
@app.post("/api/generate")
def generate():
    ip = (request.headers.get("X-Forwarded-For", request.remote_addr) or "?").split(",")[0].strip()
    if rate_limited(ip):
        return jsonify(error="Too many requests. Wait a minute and try again."), 429
 
    files = request.files.getlist("images")
    if not files:
        return jsonify(error="Upload at least one photo of your notes."), 400
    if len(files) > MAX_IMAGES:
        return jsonify(error=f"Max {MAX_IMAGES} images per kit."), 400
 
    parts = []
    for f in files:
        mime = (f.mimetype or "").lower()
        if mime not in ALLOWED_MIME:
            return jsonify(error=f"Unsupported file type: {mime or 'unknown'}"), 400
        data = f.read()
        if len(data) > MAX_IMAGE_BYTES:
            return jsonify(error="Each image must be under 6 MB."), 400
        parts.append(types.Part.from_bytes(data=data, mime_type=mime))
 
    language = request.form.get("language", "English")
    if language not in LANGUAGES:
        language = "English"
    chosen = request.form.get("model", MODEL)
    if chosen not in MODEL_LABELS:  # never pass arbitrary model names to the API
        chosen = MODEL
    n_cards = clamp(request.form.get("cards"), 3, 15, 8)
    n_quiz = clamp(request.form.get("quiz"), 3, 10, 5)
 
    prompt = PROMPT.format(language=language, n_cards=n_cards, n_quiz=n_quiz)
 
    try:
        client = get_client()
    except RuntimeError as e:
        return jsonify(error=str(e)), 500
 
    last_err = None
    for attempt in range(2):  # one retry if the model returns malformed JSON
        try:
            resp = client.models.generate_content(model=chosen, contents=[*parts, prompt])
            kit = clean_kit(extract_json(resp.text or ""))
            if not (kit["summary"] or kit["flashcards"] or kit["quiz"]):
                raise ValueError("Model returned an empty kit")
            return jsonify(kit=kit, model=chosen)
        except (ValueError, json.JSONDecodeError) as e:
            last_err = e
        except Exception as e:  # API/network errors
            app.logger.exception("Gemini API call failed")
            return jsonify(error=f"Model call failed: {e}"), 502
 
    app.logger.error("Could not parse model output: %s", last_err)
    return jsonify(error="Couldn't read that photo clearly. Try a sharper, well-lit image."), 422
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=False)
    