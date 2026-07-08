import os
import re
import shutil
import subprocess
import tempfile
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.junit_jar = os.getenv("JUNIT_JAR", "").strip()
        self._check_dependencies()

    def _check_dependencies(self):
        checks = {
            "pytest": shutil.which("pytest"),
            "node": shutil.which("node"),
            "npx": shutil.which("npx"),
            "java": shutil.which("java"),
            "javac": shutil.which("javac")
        }
        missing = [name for name, path in checks.items() if not path]
        if missing:
            logger.warning(f"Missing dependencies: {', '.join(missing)}")
        if checks.get("java") and (not self.junit_jar or not Path(self.junit_jar).exists()):
            logger.warning("JUNIT_JAR not set. Java tests will fail.")

    def run_tests(self, language, test_file_path, code_file_path=None):
        runners = {
            "python": self._run_python,
            "java": self._run_java,
            "javascript": self._run_javascript
        }
        runner = runners.get(language)
        if runner is None:
            return self._result(False, f"Unsupported language: {language}", "")
        test_file = Path(test_file_path)
        code_file = Path(code_file_path) if code_file_path else None
        if not test_file.exists():
            return self._result(False, f"Test file not found: {test_file_path}", "")
        return runner(test_file, code_file)

    def _run_python(self, test_file, code_file):
        if not shutil.which("pytest"):
            return self._result(False, "pytest is not installed. Run: pip install pytest", "")
        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            self._copy_inputs(workdir, test_file, code_file)
            try:
                result = self._run(["pytest", test_file.name, "-v", "--tb=short", "--maxfail=1"], workdir, timeout=30)
                return self._parse_pytest(result)
            except subprocess.TimeoutExpired:
                return self._result(False, "Test execution timed out (30 seconds)", "")

    def _run_javascript(self, test_file, code_file):
        if not shutil.which("node"):
            return self._result(
                False,
                "Node.js is not installed",
                "Install from https://nodejs.org/",
                additional={"fix": "npm install -g node", "alternative": "Try Python or Java instead"}
            )
        if not shutil.which("npx"):
            return self._result(False, "npm/npx is not installed", "npm usually comes with Node.js")
        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            self._copy_inputs(workdir, test_file, code_file)
            package_json = workdir / "package.json"
            if not package_json.exists():
                with open(package_json, "w") as f:
                    json.dump({"name": "testgen-test", "version": "1.0.0", "scripts": {"test": "jest"}, "devDependencies": {"jest": "^29.7.0"}}, f)
            node_modules = workdir / "node_modules"
            if not node_modules.exists():
                logger.info("Installing Jest...")
                install_result = self._run(["npm", "install", "--silent"], workdir, timeout=120)
                if install_result.returncode != 0:
                    return self._result(False, "Failed to install Jest", self._output(install_result))
            try:
                result = self._run(["npx", "jest", test_file.name, "--runInBand", "--no-coverage", "--verbose"], workdir, timeout=60)
                return self._parse_jest(result)
            except subprocess.TimeoutExpired:
                return self._result(False, "Test execution timed out (60 seconds)", "")

    def _run_java(self, test_file, code_file):
        if not shutil.which("java") or not shutil.which("javac"):
            return self._result(False, "Java JDK is not installed.", "Install OpenJDK from https://adoptium.net/")
        if not self.junit_jar or not Path(self.junit_jar).exists():
            return self._result(False, "JUnit JAR not found.", "Set JUNIT_JAR in .env")
        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            self._copy_inputs(workdir, test_file, code_file)
            java_files = [str(p) for p in workdir.glob("*.java")]
            if not java_files:
                return self._result(False, "No Java source files found", "")
            compile_result = self._run(["javac", "-cp", f".:{self.junit_jar}", *java_files], workdir, timeout=30)
            if compile_result.returncode != 0:
                return self._result(False, "Compilation failed", self._output(compile_result))
            test_class = self._java_class_name((workdir / test_file.name).read_text(encoding="utf-8"))
            if not test_class:
                return self._result(False, "Could not find test class name", "")
            try:
                result = self._run(["java", "-jar", self.junit_jar, "--class-path", str(workdir), "--select-class", test_class, "--disable-ansi-colors"], workdir, timeout=30)
                return self._parse_junit(result)
            except subprocess.TimeoutExpired:
                return self._result(False, "Test execution timed out (30 seconds)", "")

    def _copy_inputs(self, workdir, test_file, code_file):
        shutil.copy2(test_file, workdir / test_file.name)
        if code_file and code_file.exists():
            shutil.copy2(code_file, workdir / code_file.name)

    def _run(self, command, cwd, timeout=30):
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)

    def _output(self, result):
        return (result.stdout or "") + (result.stderr or "")

    def _parse_pytest(self, result):
        output = self._output(result)
        passed = self._count(r"(\d+) passed", output)
        failed = self._count(r"(\d+) failed", output)
        errors = self._count(r"(\d+) errors?", output)
        skipped = self._count(r"(\d+) skipped", output)
        return {"success": result.returncode == 0, "passed": passed, "failed": failed, "errors": errors, "skipped": skipped, "total": passed + failed + errors + skipped, "output": output}

    def _parse_jest(self, result):
        output = self._output(result)
        passed = self._count(r"(\d+) passed", output)
        failed = self._count(r"(\d+) failed", output)
        total = self._count(r"Tests:\s+(\d+)", output) or passed + failed
        return {"success": result.returncode == 0, "passed": passed, "failed": failed, "total": total or 0, "output": output}

    def _parse_junit(self, result):
        output = self._output(result)
        total = self._count(r"(\d+)\s+tests found", output)
        failed = self._count(r"(\d+)\s+tests failed", output)
        passed = max(total - failed, 0) if total else 0
        if total == 0:
            total = self._count(r"Test run:\s+(\d+)", output)
            failed = self._count(r"Failures:\s+(\d+)", output)
            passed = max(total - failed, 0) if total else 0
        return {"success": result.returncode == 0, "passed": passed, "failed": failed, "total": total or 0, "output": output}

    def _count(self, pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def _java_class_name(self, code):
        match = re.search(r"(?:public\s+)?class\s+([A-Za-z_]\w*)", code)
        return match.group(1) if match else None

    def _result(self, success, error, output, additional=None):
        result = {"success": success, "error": error, "output": output, "passed": 0, "failed": 0, "total": 0}
        if additional:
            result.update(additional)
        return result