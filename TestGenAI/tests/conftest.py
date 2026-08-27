import os
import sys
from pathlib import Path

# Make the project root importable and give AITestGenerator a key to
# initialize with, so importing app.py doesn't need real credentials or
# make network calls. Individual tests monkeypatch the generator's methods
# instead of hitting OpenAI.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Route through the Ollama code path so tests don't require the `openai`
# package or real credentials. Individual tests monkeypatch the generator's
# methods instead of making any network call.
os.environ.setdefault("USE_OLLAMA", "true")
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("FLASK_DEBUG", "false")

import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def app_instance():
    return app_module
