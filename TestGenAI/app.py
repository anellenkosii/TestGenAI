import logging
import os
import re
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from ai_generator import AITestGenerator
from code_analyzer import CodeAnalyzer
from test_runner import TestRunner

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated_tests"
UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    ai_generator = AITestGenerator()
except Exception as exc:
    logger.warning("AI generator unavailable: %s", exc)
    ai_generator = None

test_runner = TestRunner()
analyzer = CodeAnalyzer()
EXTENSIONS = {"python": "py", "java": "java", "javascript": "js"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate_tests", methods=["POST"])
def generate_tests():
    if ai_generator is None:
        return error("AI generator is not configured. Set OPENAI_API_KEY or USE_OLLAMA=true.", 500)

    language = request.form.get("language", "python")
    requirements = request.form.get("requirements", "")
    code = request.form.get("code", "").strip()
    mode = request.form.get("mode", "standard")

    if language not in EXTENSIONS:
        return error(f"Unsupported language: {language}", 400)

    uploaded = request.files.get("code_file")
    if uploaded and uploaded.filename:
        if not allowed_file(uploaded.filename, language):
            return error(f"Upload a .{EXTENSIONS[language]} file for {language}.", 400)
        code = uploaded.read().decode("utf-8", errors="replace").strip()

    if not code:
        return error("Please paste code or upload a file.", 400)

    try:
        result = ai_generator.generate_tdd_tests(language, code, requirements) if mode == "tdd" else ai_generator.generate_tests(language, code, requirements)
        tests = result.get("tests", "")
        if not tests.strip():
            return error("AI generated empty test output. Please try again.", 500)
        code_file = save_source(code, language)
        test_file = save_tests(tests, language, code)
        return jsonify(
            {
                "success": True,
                "tests": tests,
                "explanation": result.get("explanation", ""),
                "language": language,
                "test_file": test_file.name,
                "code_file": code_file.name,
            }
        )
    except Exception as exc:
        logger.exception("Generation failed")
        return error(f"AI generation failed: {exc}", 500)


@app.route("/analyze_code", methods=["POST"])
def analyze_code():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    if not code.strip():
        return error("Please provide code to analyze.", 400)
    analysis = analyzer.analyze(code, data.get("language", "python"), data.get("description", ""))
    return jsonify({"success": True, "analysis": analysis})


@app.route("/run_tests", methods=["POST"])
def run_tests():
    data = request.get_json(silent=True) or {}
    language = data.get("language", "python")
    test_path = safe_generated_path(data.get("test_file", ""))
    code_path = safe_upload_path(data.get("code_file", ""))

    if not test_path or not test_path.exists():
        return error("Test file not found.", 404)

    result = test_runner.run_tests(language, str(test_path), str(code_path) if code_path and code_path.exists() else None)
    return jsonify(result)


@app.route("/download_test/<filename>")
def download_test(filename):
    path = safe_generated_path(filename)
    if not path or not path.exists():
        return error("File not found.", 404)
    return send_file(path, as_attachment=True)


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "ai_available": ai_generator is not None})


def save_source(code, language):
    filename = f"source.{EXTENSIONS[language]}"
    if language == "java":
        filename = f"{extract_java_class_name(code) or 'Code'}.java"
    path = UPLOAD_DIR / filename
    path.write_text(code, encoding="utf-8")
    return path


def save_tests(tests, language, code):
    names = {
        "python": "test_generated.py",
        "java": f"{extract_java_class_name(code) or 'Generated'}Test.java",
        "javascript": "source.test.js",
    }
    path = GENERATED_DIR / names[language]
    path.write_text(tests, encoding="utf-8")
    return path


def allowed_file(filename, language):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == EXTENSIONS[language]


def safe_generated_path(filename):
    return safe_child(GENERATED_DIR, filename)


def safe_upload_path(filename):
    return safe_child(UPLOAD_DIR, filename)


def safe_child(parent, filename):
    if not filename:
        return None
    path = (parent / secure_filename(os.path.basename(filename))).resolve()
    return path if parent.resolve() in path.parents else None


def extract_java_class_name(code):
    match = re.search(r"(?:public\s+)?class\s+([A-Za-z_]\w*)", code)
    return match.group(1) if match else None


def error(message, status_code=400):
    return jsonify({"success": False, "error": message}), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
