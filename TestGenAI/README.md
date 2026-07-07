# TestGen AI

Flask app for generating unit tests with OpenAI or Ollama.

## Setup

```bash
cd TestGenAI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env 2>/dev/null || true
python3 app.py
```

Open `http://localhost:5000`.

## Configuration

Use OpenAI:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o
```

Use Ollama:

```env
USE_OLLAMA=true
OLLAMA_MODEL=llama3.1
OLLAMA_API_URL=http://localhost:11434/api/generate
```

Java test execution also needs:

```env
JUNIT_JAR=/absolute/path/to/junit-platform-console-standalone.jar
```

JavaScript test execution needs Node.js/npm. The app runs Jest through `npx`.
