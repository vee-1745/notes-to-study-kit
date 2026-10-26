# StudyLens: Notes to Study Kit
 
Upload photos of your handwritten notes or a textbook page. Get back a summary, key terms, flashcards and an interactive quiz, in English, Hindi or Marathi.
 
**Live demo:** https://notes-to-study-kit.onrender.com/
**Recording:** https://drive.google.com/drive/folders/1YyzhiPwTskubGrTSP_SS-op8aK4WeyAW?usp=drive_link
 
Built for the **Hacktoberfest 2026 Hack Day (Amaravati x AIBPT Club, VIT-AP)**.
 
- **Model:** Gemma 4 (open weights) through the Gemini API. It reads the photo directly, so there is no separate OCR step.
- **Model switcher:** choose Gemma 4 26B A4B (fast) or Gemma 4 31B (best quality) in the UI.
- **UI:** minimal, responsive, with System, Light and Dark themes.
- **License:** MIT
## How it works
 
1. You upload 1 to 4 photos of notes and pick a language, model and kit size.
2. The Flask backend sends the images and a structured prompt to Gemma 4.
3. Gemma 4 returns one JSON object: title, summary, key terms, flashcards, quiz.
4. The backend validates and normalises that JSON. Malformed quiz items are dropped, and unparseable output is retried once.
5. The frontend renders a summary, flip cards and a scored quiz.
```
browser --photos--> Flask /api/generate --image + prompt--> Gemma 4 (Gemini API)
   ^                      |  validate, retry once                   |
   +---- study kit JSON --+<------------ JSON study kit ------------+
```
 
## Run locally
 
macOS or Linux:
 
```bash
git clone https://github.com/vee-1745/notes-to-study-kit.git
cd notes-to-study-kit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # add your Gemini API key to .env
python app.py            # http://localhost:8080
```
 
Windows (PowerShell):
 
```powershell
git clone https://github.com/vee-1745/notes-to-study-kit.git
cd notes-to-study-kit
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # add your Gemini API key to .env
python app.py            # http://localhost:8080
```
 
Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey). Never commit your `.env` file. It is already in `.gitignore`.
 
### Configuration
 
| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | none (required) | Gemini API key |
| `GEMMA_MODEL` | `gemma-4-26b-a4b-it` | Default model. The other option is `gemma-4-31b-it` |
| `RATE_LIMIT_PER_MIN` | `6` | Per-IP requests per minute, protects the key on a public demo |
 
## Deploy (Render)
 
1. Push this repo to GitHub.
2. On [Render](https://render.com), choose **New > Web Service** and connect the repo.
3. Settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --timeout 120 -w 2 app:app`
4. Add `GEMINI_API_KEY` as an environment variable.
5. Deploy. Pushes to `main` redeploy automatically if auto-deploy is on.
The long `--timeout` matters: a vision request can take longer than gunicorn's 30 second default. Any host that runs gunicorn works. A `Procfile` is included for Heroku-style platforms.
 
## Project layout
 
```
app.py                Flask app, Gemma 4 call, output validation, rate limit
templates/index.html  Single-page UI (vanilla JS, no build step)
requirements.txt      Python dependencies
Procfile              gunicorn command for Heroku-style hosts
.env.example          Example configuration
```
 
## Limitations
 
- Output quality depends on photo clarity. Blurry or dim photos may fail or give thin kits.
- The kit is generated only from what is visible in the notes, but a language model can still make mistakes. Check important facts against your textbook.
- Gemma models on the Gemini API have low free-tier limits, so heavy use can hit quota errors. Switching models in the UI can help.
- The rate limiter is in-memory and per instance. It is a guard for a demo, not a production control.
- On a free Render instance the first request after a quiet period can take about a minute while the app wakes up.
## Contributing
 
Issues and PRs are welcome, and the project is Hacktoberfest friendly. Good first issues: PDF input, export flashcards to Anki, more languages, saved kits, a test suite.