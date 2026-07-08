import logging
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

class AITestGenerator:
    def __init__(self):
        self.use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = None
        
        if not self.use_ollama:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if not api_key or api_key == "your_openai_api_key_here":
                raise ValueError("OpenAI API key not set. Please check your .env file.")
            # New v1.0+ syntax
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully (v1.0+)")

    def generate_tests(self, language, code, requirements=""):
        prompt = self._build_prompt(language, code, requirements, tdd=False)
        tests = self._clean_response(self._call_ai(prompt))
        return {"tests": tests, "explanation": self._explain(tests, language, tdd=False)}

    def generate_tdd_tests(self, language, code, requirements=""):
        prompt = self._build_prompt(language, code, requirements, tdd=True)
        tests = self._clean_response(self._call_ai(prompt))
        return {"tests": tests, "explanation": self._explain(tests, language, tdd=True)}

    def _call_ai(self, prompt):
        if self.use_ollama:
            return self._call_ollama(prompt)
        try:
            # New v1.0+ syntax
            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "Return only runnable unit test code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2500,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise RuntimeError(f"AI API error: {exc}") from exc

    def _call_ollama(self, prompt):
        import requests
        response = requests.post(
            os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate"),
            json={
                "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,
                "max_tokens": 2500,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")

    def _build_prompt(self, language, code, requirements, tdd):
        config = {
            "python": {"framework": "pytest", "extra": "Import from source.py. Cover normal cases, edge cases, and errors."},
            "java": {"framework": "JUnit 5", "extra": "Use org.junit.jupiter.api.Test and assertions. Do not include package declarations."},
            "javascript": {"framework": "Jest", "extra": "Use CommonJS require('./source') if the source exports functions."},
        }
        details = config.get(language, config["python"])
        mode = "test-driven development tests before implementation" if tdd else "unit tests"
        req = requirements.strip() or "Infer expected behavior from the code."
        return f"""Generate comprehensive {details['framework']} {mode} for this {language} code.

Requirements:
{req}

Rules:
- Return only test code, no markdown or explanations.
- Include necessary imports.
- Make the file runnable.
- Include happy path, edge case, and error handling tests.
- {details['extra']}

Source code:
```{language}
{code}
```"""

    def _clean_response(self, text):
        text = (text or "").strip()
        match = re.search(r"```(?:python|java|javascript|js)?\s*(.*?)```", text, re.DOTALL)
        return (match.group(1) if match else text).strip()

    def _explain(self, tests, language, tdd):
        mode = "TDD" if tdd else "standard"
        count = len(re.findall(r"\b(test_|@Test|it\(|test\()", tests))
        coverage = []
        if re.search(r"(assert|assertEquals|expect)", tests):
            coverage.append("✅ Assertions")
        if re.search(r"(raises|assertThrows|throw)", tests):
            coverage.append("✅ Exception handling")
        if re.search(r"(edge|boundary|zero|empty|null)", tests.lower()):
            coverage.append("✅ Edge cases")
        return f"""Generated {mode} {language} tests.

Estimated test cases: {count or 'unknown'}
Coverage areas: {', '.join(coverage) if coverage else 'Basic tests'}

💡 Student Notes:
- Read each test carefully - understand WHY it exists
- Run tests step by step to learn debugging
"""
