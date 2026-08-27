# TestGen AI

AI-powered unit test generator for Python, Java, and JavaScript.

## Overview

TestGen AI is a Flask web app that generates unit tests for pasted or
uploaded code, using OpenAI's API or a local Ollama model. It also runs a
quick heuristic pre-check on submitted code, and can execute the generated
tests directly and show pass/fail results.

### Target users

- Software students learning testing practices through examples
- Junior QA engineers looking to speed up test writing
- Developers who want to skip boilerplate test code

### Features

- AI-powered generation using OpenAI GPT-4o or local Ollama
- Python (pytest), Java (JUnit 5), and JavaScript (Jest) support
- Paste code or upload a file
- Standard or TDD-style generation
- In-browser test execution with pass/fail counts
- Heuristic pre-check that scores code on test-coverage indicators before you
  spend an AI call on it

## Quick start

### Prerequisites

- Python 3.11+
- An OpenAI API key **or** a local Ollama install
- Node.js + npm (only needed to run generated JavaScript tests)
- Java JDK 17+ (only needed to run generated Java tests)

### Install

```bash
git clone https://github.com/<your-username>/TestGenAI.git
cd TestGenAI

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env with your API key
```

### Run

```bash
python3 app.py
# open http://localhost:5002
```

### Run the app's own test suite

```bash
pip install -r requirements-dev.txt
pytest
```

## Configuration

**Option 1 — OpenAI (cloud)**

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
USE_OLLAMA=false
```

**Option 2 — Ollama (local, free)**

```env
USE_OLLAMA=true
OLLAMA_MODEL=llama3.1
OLLAMA_API_URL=http://localhost:11434/api/generate
```

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1
ollama serve
```

**Java test execution (optional)**

```bash
wget -O junit-platform-console-standalone-1.10.2.jar \
  https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar
```

Set `JUNIT_JAR=/path/to/that/jar` in `.env`.

### Docker

```bash
docker compose up --build
# open http://localhost:5002
```

The container already includes the Java and Node toolchains and downloads
the JUnit jar at build time, so Java/JS test execution works out of the box
there even if you don't have them installed locally.

## Project structure

```
testgenai/
├── app.py                 # Flask routes
├── ai_generator.py        # AI test generation (OpenAI / Ollama)
├── test_runner.py         # Executes generated tests
├── code_analyzer.py       # Heuristic pre-check, no AI call
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── templates/index.html
├── static/{style.css, app.js}
├── examples/               # sample source files for each language
└── tests/                 # pytest suite for this app
```

## Security notes / known limitations

This is a portfolio/demo project, and it does something inherently risky:
**it runs code it didn't write** — AI-generated tests, and whatever source
the user pasted or uploaded — using the real pytest/npm/java toolchains on
the host. That's what "run tests in the browser" requires, but it's worth
being explicit about the tradeoffs:

- **Not containerized per-request.** Each run happens in a fresh temp
  directory, but on the same host process. A determined malicious input
  could still do things a sandboxed request couldn't. For anything beyond a
  local demo, isolate each run in its own container or VM.
- **Mitigations that are in place:** subprocesses run with a minimal
  environment (no API keys or host secrets in `os.environ`), CPU-time and
  memory limits on POSIX systems, a 30–120 second timeout per run, and
  `npm install --ignore-scripts` to stop `package.json` install scripts
  from executing.
- **Prompt injection:** code submitted for test generation is treated as
  untrusted input in the AI prompt (the prompt explicitly tells the model to
  ignore instructions embedded in the source), but this is a mitigation, not
  a guarantee.
- **Path handling:** uploaded/generated filenames are sanitized and resolved
  against their parent directory to block path traversal on
  download/execution endpoints.

If you're using this project to demonstrate QA thinking, this section is
arguably as valuable as the code itself — it shows you can reason about
what could go wrong with a tool like this, not just get it working.

## Error handling

| Error type | Response |
|---|---|
| Missing API key | "AI generator not initialized" |
| Invalid/oversized code | Clear error message, request rejected before an AI call |
| Test failure | Detailed failure output |
| Network issues | Connection error message |
| File upload error | Supported file types listed |

## Tech stack

**Backend:** Flask, OpenAI API / Ollama, pytest / JUnit 5 / Jest, Python 3.11+
**Frontend:** HTML/CSS, vanilla JavaScript, Prism.js for syntax highlighting

## License

MIT — see [LICENSE](LICENSE).
