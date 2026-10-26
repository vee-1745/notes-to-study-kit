# Notes to Study Kit

**Tagline:** Photograph your notes, get a summary, flashcards and a quiz in English, Hindi or Marathi.

**Prize categories:** Best Use of Gemma 4 | Best Open-Source AI Project (DigitalOcean)

**Links**
- Live demo: `<DigitalOcean app URL>`
- GitHub: `https://github.com/YOUR_GITHUB_USERNAME/notes-to-study-kit`
- Demo video: `<link, if recorded>`

---

## Inspiration

Students already take photos of notes, whiteboards and textbook pages. Those photos pile up in a camera roll and never turn into revision. Making flashcards and practice questions by hand takes longer than the studying itself, so most people skip it. We wanted a tool where the photo is the only input.

We also wanted it to work in the languages students actually think in. Many of us read English notes but revise more comfortably in Hindi or Marathi, so the kit can be generated in any of the three.

## What it does

Upload one to four photos of handwritten notes or a printed page. Notes to Study Kit returns:

- a short title and a bullet-point **summary**
- **key terms** with definitions
- **flashcards** you can flip through
- an interactive **multiple-choice quiz** with instant feedback, explanations and a score

You choose the output language (English, Hindi, Marathi) and how many flashcards and questions you want. The kit is built only from what is visible in the photos, so it studies your notes, not the internet's version of the topic.

## How we built it

- **Gemma 4** is the core of the app. It runs through the Gemini API and reads the note photos directly, so there is no separate OCR step. One multimodal call turns the image into a structured study kit. We use `gemma-4-26b-a4b-it` by default and `gemma-4-31b-it` as a higher-quality option, switchable with one environment variable.
- **Flask backend** with a structured prompt that asks for one JSON object. The server then validates it: it checks every quiz question has exactly four options and a valid answer index, drops malformed items, and retries once if the JSON can't be parsed.
- **Vanilla HTML/CSS/JS frontend** with no build step: drag-and-drop upload, flip cards, and a scored quiz, with light and dark themes.
- **DigitalOcean App Platform** hosts it with gunicorn, deployed straight from the GitHub repo, so every push to `main` redeploys. The API key is stored as an encrypted environment variable.
- **Open source under MIT**, with a README, `.env.example`, deploy spec and contribution ideas.

## Challenges we ran into

- **Getting dependable structured output from an open model.** The model sometimes wraps JSON in markdown fences or adds a sentence before it. We extract the JSON object defensively, validate every field, and retry once before showing an error.
- **Trusting the output.** A study tool that invents facts is worse than none. The prompt tells the model to use only what the notes say and skip anything unreadable, and the UI reminds students to check important facts.
- **Protecting a public demo.** An open endpoint backed by an API key can be drained, so we added file type and size limits and a per-IP rate limit.
- **Multilingual quizzes.** Keeping the questions, options and explanations all in the chosen language, while the answer index stays machine-readable, needed a strict output schema.

## Accomplishments that we're proud of

- A single photo becomes four different study formats in one model call.
- It works end to end on a free-tier setup: Gemma 4 through the Gemini API and a small DigitalOcean instance.
- The app is small enough to read in one sitting, which makes it a good base for contributors.

## What we learned

- Gemma 4's image understanding is good enough to replace a separate OCR pipeline for typical note photos.
- With open-weight models, the validation layer around the model matters as much as the prompt.
- App Platform's push-to-deploy flow makes it easy to ship a hackathon project and keep iterating after it.

## What's next

- PDF and multi-page document input
- Export flashcards to Anki
- Saved kits and spaced-repetition scheduling
- More languages
- Self-hosting Gemma 4 on a DigitalOcean GPU Droplet instead of using the hosted API

## Built with

Gemma 4, Gemini API, Python, Flask, gunicorn, HTML/CSS/JavaScript, DigitalOcean App Platform, GitHub

---

### Notes before you submit (delete this section)

- Replace every `<...>` and `YOUR_GITHUB_USERNAME` placeholder.
- Add 2 or 3 screenshots: the upload screen, a flip card, a finished quiz.
- Try it with a real photo before the demo and edit "Challenges" so it matches what you actually hit today. The challenges above describe design decisions in the code, not bugs from live testing.
- Add teammates' names if you built it as a team.
