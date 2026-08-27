import os
import re
import json
import logging
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        """Allow diagnostics/tests to import the app before dependencies are installed."""
        return False

try:
    from flask import Flask, jsonify, render_template, request, send_file
    from werkzeug.utils import secure_filename
    _HAS_FRAMEWORK = True
except Exception:
    # Provide tiny fallbacks so the module can be imported without
    # installing Flask/Werkzeug in constrained environments (tests
    # will exercise a subset of behavior).
    _HAS_FRAMEWORK = False

    def secure_filename(filename: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", filename).strip("._")

    def render_template(name: str, **_kwargs):
        tpl = Path(__file__).resolve().parent / "templates" / name
        if tpl.exists():
            return tpl.read_text(encoding="utf-8")
        return "<html><body>TestGen AI</body></html>"

    def send_file(path, as_attachment=False):
        p = Path(path)
        if not p.exists():
            return make_response({"success": False, "error": "File not found."}, 404)
        return make_response(p.read_bytes(), 200)

    class _Request:
        def __init__(self):
            self.form = {}
            self.files = {}
            self._json = None

        def get_json(self, silent=False):
            return self._json

    request = _Request()

    def jsonify(obj):
        return (json.dumps(obj).encode("utf-8"), 200, {"Content-Type": "application/json"})

    def make_response(body, status=200, headers=None):
        class Resp:
            def __init__(self, body, status, headers):
                self.status_code = status
                self._body = body
                self.headers = headers or {}

            @property
            def data(self):
                return self._body if isinstance(self._body, (bytes, bytearray)) else str(self._body).encode("utf-8")

            def get_json(self):
                try:
                    return json.loads(self._body.decode("utf-8"))
                except Exception:
                    return None

        return Resp(body, status, headers)

    # Minimal route/app/testing harness used only when Flask isn't available.
    class FlaskCompat:
        def __init__(self, name):
            self._routes = {}
            self.config = {}

        def route(self, path, methods=None):
            def _decor(fn):
                self._routes[path] = (fn, methods or ["GET"])
                return fn

            return _decor

        def test_client(self):
            app = self

            class Client:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def _call(self, method, path, data=None, json_data=None):
                    fn_tuple = app._routes.get(path)
                    if not fn_tuple:
                        resp = make_response(json.dumps({"success": False, "error": "Not Found"}).encode("utf-8"), 404)
                        return resp
                    fn, methods = fn_tuple
                    # populate fake request
                    request.form = data or {}
                    request.files = {}
                    request._json = json_data
                    try:
                        rv = fn()
                    except TypeError:
                        rv = fn()
                    if isinstance(rv, tuple) and len(rv) == 2 and isinstance(rv[0], (bytes, str, dict)):
                        body, status = rv
                        if isinstance(body, dict):
                            return make_response(json.dumps(body).encode("utf-8"), status)
                        if isinstance(body, str):
                            return make_response(body.encode("utf-8"), status)
                        return make_response(body, status)
                    if hasattr(rv, "status_code"):
                        return rv
                    if isinstance(rv, dict):
                        return make_response(json.dumps(rv).encode("utf-8"), 200)
                    if isinstance(rv, tuple) and len(rv) == 3:
                        # (body, status, headers)
                        body, status, headers = rv
                        return make_response(body, status, headers)
                    return make_response(rv, 200)

                def get(self, path):
                    return self._call("GET", path)

                def post(self, path, data=None, json=None):
                    return self._call("POST", path, data=data, json_data=json)

            return Client()

        def run(self, *_args, **_kwargs):
            raise RuntimeError(
                "Flask and Werkzeug are required to run the web app. "
                "Install them with: pip install -r requirements.txt"
            )

    Flask = FlaskCompat

    # helper used by our error responses
    def make_error(message, status_code=400):
        return (json.dumps({"success": False, "error": message}).encode("utf-8"), status_code, {"Content-Type": "application/json"})

    # alias used later in the module
    error = lambda m, s=400: make_error(m, s)

from ai_generator import AITestGenerator
from test_runner import TestRunner
from code_analyzer import CodeAnalyzer

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated_tests"
UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

MAX_CODE_LENGTH = 20_000  # characters, keeps AI prompt size and test-run time bounded

app = Flask(__name__)
# load environment from .env if present
try:
    load_dotenv()
except Exception:
    # ignore when dotenv isn't available (tests provide a shim)
    pass
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or os.urandom(32).hex()
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["GENERATED_TESTS_FOLDER"] = str(GENERATED_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    ai_generator = AITestGenerator()
    logger.info("AI generator initialized")
except Exception as exc:
    logger.error("AI generator failed to initialize: %s", exc)
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
        return error("AI generator not initialized. Check your API configuration.", 500)

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
        except Exception as exc:
            return error(f"Failed to read file: {exc}", 400)

    if not code:
        return error("Please paste code or upload a file.", 400)
    if len(code) > MAX_CODE_LENGTH:
        return error(f"Code is too long ({len(code)} chars). Limit is {MAX_CODE_LENGTH}.", 400)

    try:
        if mode == "tdd":
            result = ai_generator.generate_tdd_tests(language, code, requirements)
        else:
            result = ai_generator.generate_tests(language, code, requirements)
    except Exception as exc:
        logger.error("AI generation failed: %s", exc)
        return error(f"AI generation failed: {exc}", 502)

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
            "code_file": code_file.name,
        })
    except Exception as exc:
        logger.error("File save failed: %s", exc)
        return error(f"Failed to save files: {exc}", 500)


@app.route("/analyze_code", methods=["POST"])
def analyze_code():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    language = data.get("language", "python")
    description = data.get("description", "")

    if language not in EXTENSIONS:
        return error(f"Unsupported language: {language}", 400)
    if not code:
        return error("Please provide code to analyze.", 400)
    if len(code) > MAX_CODE_LENGTH:
        return error(f"Code is too long ({len(code)} chars). Limit is {MAX_CODE_LENGTH}.", 400)

    try:
        analysis = analyzer.analyze(code, language, description)
        return jsonify({"success": True, "analysis": analysis})
    except Exception as exc:
        logger.error("Analysis failed: %s", exc)
        return error(f"Analysis failed: {exc}", 500)


@app.route("/run_tests", methods=["POST"])
def run_tests():
    data = request.get_json(silent=True) or {}
    language = data.get("language", "python")
    test_file = data.get("test_file", "")
    code_file = data.get("code_file", "")

    if language not in EXTENSIONS:
        return error(f"Unsupported language: {language}", 400)
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
            code_file_path=str(code_path) if code_path else None,
        )
        return jsonify(result)
    except Exception as exc:
        logger.error("Test execution failed: %s", exc)
        return error(f"Test execution failed: {exc}", 500)


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
    """Resolve filename under parent, rejecting traversal outside of it."""
    if not filename:
        return None
    filename = os.path.basename(filename)
    path = (parent / secure_filename(filename)).resolve()
    return path if parent.resolve() in path.parents else None


def extract_java_class_name(code):
    match = re.search(r"(?:public\s+)?class\s+([A-Za-z_]\w*)", code)
    return match.group(1) if match else None


def error(message, status_code=400):
    if not _HAS_FRAMEWORK:
        return make_error(message, status_code)
    return jsonify({"success": False, "error": message}), status_code


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5002"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
