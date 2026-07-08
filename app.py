import os
import re
import logging
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename
from ai_generator import AITestGenerator
from test_runner import TestRunner
from code_analyzer import CodeAnalyzer

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated_tests"
UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["GENERATED_TESTS_FOLDER"] = str(GENERATED_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    ai_generator = AITestGenerator()
    logger.info("AI Generator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AI Generator: {str(e)}")
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
        return error("AI Generator not initialized. Check your API configuration.", 500)
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
        try:
            code = uploaded.read().decode("utf-8", errors="replace").strip()
        except Exception as e:
            return error(f"Failed to read file: {str(e)}", 400)
    if not code:
        return error("Please paste code or upload a file.", 400)
    try:
        if mode == "tdd":
            result = ai_generator.generate_tdd_tests(language, code, requirements)
        else:
            result = ai_generator.generate_tests(language, code, requirements)
    except Exception as exc:
        logger.error(f"AI generation failed: {str(exc)}")
        return error(f"AI generation failed: {str(exc)}", 500)
    try:
        tests = result.get("tests", "")
        explanation = result.get("explanation", "")
        test_file = save_tests(tests, language, code)
        code_file = save_source(code, language)
        return jsonify({
            "success": True,
            "tests": tests,
            "explanation": explanation,
            "language": language,
            "test_file": test_file.name,
            "code_file": code_file.name
        })
    except Exception as e:
        logger.error(f"File save failed: {str(e)}")
        return error(f"Failed to save files: {str(e)}", 500)

@app.route("/analyze_code", methods=["POST"])
def analyze_code():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    language = data.get("language", "python")
    description = data.get("description", "")
    if not code:
        return error("Please provide code to analyze.", 400)
    try:
        analysis = analyzer.analyze(code, language, description)
        return jsonify({"success": True, "analysis": analysis})
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return error(f"Analysis failed: {str(e)}", 500)

@app.route("/run_tests", methods=["POST"])
def run_tests():
    data = request.get_json(silent=True) or {}
    language = data.get("language", "python")
    test_file = data.get("test_file", "")
    code_file = data.get("code_file", "")
    if not test_file:
        return error("No test file specified", 400)
    test_path = safe_generated_path(test_file)
    if not test_path or not test_path.exists():
        return error(f"Test file not found: {test_file}", 404)
    code_path = safe_upload_path(code_file) if code_file else None
    if code_path and not code_path.exists():
        code_path = None
    try:
        result = test_runner.run_tests(
            language=language,
            test_file_path=str(test_path),
            code_file_path=str(code_path) if code_path else None
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        return error(f"Test execution failed: {str(e)}", 500)

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
        class_name = extract_java_class_name(code)
        filename = f"{class_name or 'Code'}.java"
    path = UPLOAD_DIR / filename
    path.write_text(code, encoding="utf-8")
    return path

def save_tests(tests, language, code):
    names = {
        "python": "test_generated.py",
        "java": f"{extract_java_class_name(code) or 'Generated'}Test.java",
        "javascript": "source.test.js"
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
    filename = os.path.basename(filename)
    path = (parent / secure_filename(filename)).resolve()
    return path if parent.resolve() in path.parents else None

def extract_java_class_name(code):
    match = re.search(r"(?:public\s+)?class\s+([A-Za-z_]\w*)", code)
    return match.group(1) if match else None

def error(message, status_code=400):
    return jsonify({"success": False, "error": message}), status_code

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5002"))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
