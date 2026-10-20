# Studyspace · AI study companion

Studyspace turns the familiar tutor-bot project into a focused study workspace. Ask an AI tutor questions, upload class materials, and review automatically generated flashcards in a calm, responsive interface that keeps the Society of Women Engineers (SWE) logo.

## Features

- AI tutoring conversations with saved session history
- Flashcard generation from PDF, DOCX, and TXT uploads
- Click-to-reveal flashcards with deck navigation
- Responsive chat, flashcard, and about views
- FastAPI backend with a lightweight, dependency-free JavaScript frontend

## Run locally

### 1. Configure the AI service

Set the Groq API key expected by `server/services/groq_client.py` in `server/.env`:

```env
GROQ_API_KEY=your-groq-api-key
# Optional: defaults to openai/gpt-oss-120b
GROQ_MODEL=openai/gpt-oss-120b
```

### 2. Start the API

```powershell
cd server
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

The API is available at `http://localhost:8080`. Its interactive API documentation is at `http://localhost:8080/docs`.

### 3. Serve the frontend

Open a second terminal from the project root:

```powershell
cd client
python -m http.server 5500
```

Open `http://localhost:5500`. The browser frontend connects to the API on port `8080`.

## Project structure

```text
client/                 Responsive JavaScript, HTML, styles, and SWE brand assets
  components/           Reusable chat and flashcard views
server/                 FastAPI application and AI/document services
  conversations/        Local JSON conversation history
  routers/              Chat and flashcard API routes
  services/             Groq client, document extraction, card generation
```

## API routes

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/chat` | Send a message to a named tutor conversation |
| `GET` | `/conversations` | List saved conversation sessions |
| `GET` | `/conversations/{chat_name}` | Load a conversation and its messages |
| `POST` | `/flashcards` | Extract study material and generate flashcards |

## Tech stack

Vanilla JavaScript, semantic HTML, responsive CSS, Python, FastAPI, Groq, and document parsing with pypdf and python-docx.
