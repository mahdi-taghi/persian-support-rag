# Chatbot support stack

Minimal Django API + optional Next.js UI. Follow the steps in order.

---

## What you need installed

| Tool             | Why                                 |
| ---------------- | ----------------------------------- |
| **Python 3.11+** | Runs the backend and AI code        |
| **Node.js 20+**  | Only if you use the included web UI |

---

## 1. Get the code

```bash
git clone <your-repo-url>
cd chatbot-assistant
```

---

## 2. Python environment & packages

From the **project root** (`chatbot-assistant`):

```bash
python3 -m venv .venv
```

Activate it:

- **macOS / Linux:** `source .venv/bin/activate`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

_(Only if you use `AI/scrap/` Playwright scripts: run `playwright install` once.)_

---

## 3. Configure secrets (`AI/.env`)

Copy the example file and edit it:

```bash
cp AI/.env.example AI/.env
```

Open `AI/.env` and set real values:

- `METIS_API_KEY` — your API key
- `METIS_OPENAI_BASE_URL` — OpenAI-compatible base URL
- `METIS_REST_API_ENDPOINT` — Gemini REST endpoint (used for handoff logic)

Save the file.

---

## 4. Vector database (required for answers)

The bot reads help articles from **ChromaDB** under `AI/chroma_db/` (collection name: `binance_help_docs`).

- If you already have this folder from your team, put it at `AI/chroma_db/` and skip ahead.
- If you don’t have it, you must build it using your own data pipeline (for example `AI/embed.py` and your JSONL chunks). Without it, the API may error when answering.

---

## 5. Database & start the API

All commands below use the **backend** app folder:

```bash
cd backend
```

Create/update the SQLite DB:

```bash
python manage.py migrate
```

Start the server:

```bash
python manage.py runserver
```

Leave this terminal open. The API is now at **http://127.0.0.1:8000/**.

---

## 6. web UI (Next.js)

Open a **second** terminal, project root:

```bash
cd frontend
npm install
npm run dev
```

or

```bash
cd frontend
npm install
npm run build
npm start
```

Open **http://localhost:3000** in your browser — type a message and press send; the reply appears in the chat window.

If the UI cannot reach the API, set:

```bash
export NEXT_PUBLIC_API_ORIGIN=http://127.0.0.1:8000
```

(or the equivalent on Windows), then run `npm run dev` again.

---

## Quick checklist

1. `pip install -r requirements.txt`
2. Fill `AI/.env`
3. Ensure `AI/chroma_db/` exists
4. `cd backend` → `python manage.py migrate` → `python manage.py runserver`
5. Test with `curl` / PowerShell or open the Next.js app

If something fails, read the error in the terminal running `runserver` — it usually says what is missing (env var, Chroma path, etc.).
