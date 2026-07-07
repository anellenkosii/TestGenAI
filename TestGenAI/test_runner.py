# test_runner.py - Complete updated version with better error handling and Jest support
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
        """Initialize the test runner with configuration"""
        self.junit_jar = os.getenv("JUNIT_JAR", "").strip()
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required tools are available"""
        checks = {
            "pytest": shutil.which("pytest"),
            "node": shutil.which("node"),
            "npx": shutil.which("npx"),
            "java": shutil.which("java"),
            "javac": shutil.which("javac"),
        }
        
        missing = [name for name, path in checks.items() if not path]
        if missing:
            logger.warning(f"Missing dependencies: {', '.join(missing)}")
        
        # Check JUnit JAR for Java testing
        if checks.get("java") and (not self.junit_jar or not Path(self.junit_jar).exists()):
            logger.warning("JUNIT_JAR not set or not found. Java tests will fail.")
            # Try to find it in common locations
            common_paths = [
                "lib/junit-platform-console-standalone-1.10.2.jar",
                "/usr/share/java/junit-platform-console-standalone.jar",
            ]
            for path in common_paths:
                if Path(path).exists():
                    self.junit_jar = path
                    logger.info(f"Found JUnit JAR at: {path}")
                    break

    def run_tests(self, language, test_file_path, code_file_path=None):
        """Run tests for the specified language"""
        runners = {
            "python": self._run_python,
            "java": self._run_java,
            "javascript": self._run_javascript,
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
        """Run Python tests using pytest"""
        if not shutil.which("pytest"):
            return self._result(False, "pytest is not installed. Run: pip install pytest", "")

        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            self._copy_inputs(workdir, test_file, code_file)
            
            # Try to run pytest
            try:
                result = self._run(
                    ["pytest", test_file.name, "-v", "--tb=short", "--maxfail=1"],
                    workdir,
                    timeout=30
                )
                return self._parse_pytest(result)
            except subprocess.TimeoutExpired:
                return self._result(False, "Test execution timed out (30 seconds)", "")

    def _run_javascript(self, test_file, code_file):
        """Run JavaScript tests using Jest"""
        if not shutil.which("npx"):
            return self._result(False, "Node.js/npm is not installed.", "")

        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            self._copy_inputs(workdir, test_file, code_file)
            
            # Create package.json if it doesn't exist
            package_json = workdir / "package.json"
            if not package_json.exists():
                with open(package_json, "w") as f:
                    json.dump({
                        "name": "testgen-test",
                        "version": "1.0.0",
                        "scripts": {"test": "jest"},
                        "devDependencies": {"jest": "^29.7.0"}
                    }, f)
            
            # Install Jest if needed
            node_modules = workdir / "node_modules"
            if not node_modules.exists():
                logger.info("Installing Jest (this may take a moment)...")
                install_result = self._run(["npm", "install", "--silent"], workdir, timeout=120)
                if install_result.returncode != 0:
                    return self._result(False, "Failed to install Jest", self._output(install_result))
            
            # Run Jest
            try:
                result = self._run(
                    ["npx", "jest", test_file.name, "--runInBand", "--no-coverage", "--verbose"],
                    workdir,
                    timeout=60
                )
                return self._parse_jest(result)
            except subprocess.TimeoutExpired:
                return self._result(False, "Test execution timed out (60 seconds)", "")

    def _run_java(self, test_file, code_file):
        """Run Java tests using JUnit 5"""
        if not shutil.which("java") or not shutil.which("javac"):
            return self._result(False, "Java JDK is not installed.", "")

        if not self.junit_jar or not Path(self.junit_jar).exists():
            return self._result(
                False,
                "JUnit JAR not found. Set JUNIT_JAR to the path of junit-platform-console-standalone.jar",
                ""
            )

        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            self._copy_inputs(workdir, test_file, code_file)
            
            # Get all Java files
            java_files = [str(p) for p in workdir.glob("*.java")]
            if not java_files:
                return self._result(False, "No Java source files found", "")
            
            # Compile Java files
            compile_result = self._run(
                ["javac", "-cp", f".:{self.junit_jar}", *java_files],
                workdir,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return self._result(False, "Compilation failed", self._output(compile_result))
            
            # Extract test class name
            test_class = self._java_class_name((workdir / test_file.name).read_text(encoding="utf-8"))
            if not test_class:
                return self._result(False, "Could not find test class name", "")
            
            # Run JUnit tests
            try:
                result = self._run(
                    [
                        "java",
                        "-jar",
                        self.junit_jar,
                        "--class-path",
                        str(workdir),
                        "--select-class",
                        test_class,
                        "--disable-ansi-colors",
                    ],
                    workdir,
                    timeout=30
                )
                return self._parse_junit(result)
            except subprocess.TimeoutExpired:
                return self._result(False, "Test execution timed out (30 seconds)", "")

    def _copy_inputs(self, workdir, test_file, code_file):
        """Copy input files to the working directory"""
        shutil.copy2(test_file, workdir / test_file.name)
        if code_file and code_file.exists():
            shutil.copy2(code_file, workdir / code_file.name)

    def _run(self, command, cwd, timeout=30):
        """Run a subprocess with timeout"""
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    def _output(self, result):
        """Get combined output from a subprocess result"""
        return (result.stdout or "") + (result.stderr or "")

    def _parse_pytest(self, result):
        """Parse pytest output"""
        output = self._output(result)
        
        # Extract test results
        passed = self._count(r"(\d+) passed", output)
        failed = self._count(r"(\d+) failed", output)
        errors = self._count(r"(\d+) errors?", output)
        skipped = self._count(r"(\d+) skipped", output)
        
        return {
            "success": result.returncode == 0,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "total": passed + failed + errors + skipped,
            "output": output,
        }

    def _parse_jest(self, result):
        """Parse Jest output"""
        output = self._output(result)
        
        passed = self._count(r"(\d+) passed", output)
        failed = self._count(r"(\d+) failed", output)
        total = self._count(r"Tests:\s+(\d+)", output)
        
        if total == 0:
            # Try to count individual tests
            total = passed + failed
        
        return {
            "success": result.returncode == 0,
            "passed": passed,
            "failed": failed,
            "total": total or 0,
            "output": output,
        }

    def _parse_junit(self, result):
        """Parse JUnit output"""
        output = self._output(result)
        
        total = self._count(r"(\d+)\s+tests found", output)
        failed = self._count(r"(\d+)\s+tests failed", output)
        passed = max(total - failed, 0) if total else 0
        
        # If no tests found, try alternative parsing
        if total == 0:
            total = self._count(r"Test run:\s+(\d+)", output)
            failed = self._count(r"Failures:\s+(\d+)", output)
            passed = max(total - failed, 0) if total else 0
        
        return {
            "success": result.returncode == 0,
            "passed": passed,
            "failed": failed,
            "total": total or 0,
            "output": output,
        }

    def _count(self, pattern, text):
        """Count occurrences of a pattern in text"""
        match = re.search(pattern, text, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def _java_class_name(self, code):
        """Extract class name from Java code"""
        match = re.search(r"(?:public\s+)?class\s+([A-Za-z_]\w*)", code)
        return match.group(1) if match else None

    def _result(self, success, error, output):
        """Create a standardized result object"""
        return {
            "success": success,
            "error": error,
            "output": output,
            "passed": 0,
            "failed": 0,
            "total": 0,
        }