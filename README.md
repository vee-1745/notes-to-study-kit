# Notes to Study Kit

Snap a photo of your handwritten notes or a textbook page. Get back a summary, key terms, flashcards and an interactive quiz, in English, Hindi or Marathi.

Built for **Hacktoberfest 2026 Hack Day (Amaravati x AIBPT Club, VIT-AP)**.

- **Model:** Gemma 4 (open weights), called through the Gemini API. It reads the photo directly, so there is no separate OCR step.
- **Hosting:** DigitalOcean App Platform, deployed from this repo.
- **License:** MIT

## How it works

1. You upload 1 to 4 photos of notes.
2. The Flask backend sends the images and a structured prompt to Gemma 4.
3. Gemma 4 returns one JSON object: title, summary, key terms, flashcards, quiz.
4. The backend validates and normalises that JSON (bad quiz items are dropped, malformed output is retried once).
5. The frontend renders a summary view, flip-cards and a scored quiz.

```
browser  --photos-->  Flask /api/generate  --image + prompt-->  Gemma 4 (Gemini API)
   ^                         |  validate + retry once                    |
   +------ study kit JSON ---+<------------- JSON study kit -------------+
```

## Run locally

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/notes-to-study-kit.git
cd notes-to-study-kit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your Gemini API key in .env
python app.py               # http://localhost:8080
```

Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey).

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | none (required) | Gemini API key |
| `GEMMA_MODEL` | `gemma-4-26b-a4b-it` | Use `gemma-4-31b-it` for higher quality |
| `RATE_LIMIT_PER_MIN` | `6` | Per-IP requests per minute, protects the key on a public demo |

## Deploy to DigitalOcean App Platform

1. Push this repo to GitHub (public).
2. In the DigitalOcean control panel: **Create > App Platform > GitHub**, pick this repo and the `main` branch.
3. Run command (usually auto-detected from the `Procfile`):
   `gunicorn --worker-tmp-dir /dev/shm -w 2 -b 0.0.0.0:8080 --timeout 120 app:app`
4. HTTP port `8080`. Add `GEMINI_API_KEY` as an encrypted environment variable.
5. Deploy. Every push to `main` redeploys automatically.

Or with the CLI, after editing the repo name in `.do/app.yaml`:

```bash
doctl apps create --spec .do/app.yaml
```

## Project layout

```
app.py              Flask app, Gemma 4 call, output validation, rate limit
templates/index.html  Single-page UI (vanilla JS, no build step)
.do/app.yaml        DigitalOcean App Platform spec
Procfile            gunicorn start command
requirements.txt    Python dependencies
```

## Limitations

- Quality depends on photo clarity. Blurry or very dim photos may fail or give thin kits.
- The kit is generated only from what is visible in the notes, but a language model can still make mistakes. Check important facts against your textbook.
- The rate limiter is in-memory and per-instance. It is a guard for a demo, not a production control.

## Contributing

Issues and PRs are welcome (Hacktoberfest friendly). Good first issues: PDF input, export flashcards to Anki, more languages, saved kits.
