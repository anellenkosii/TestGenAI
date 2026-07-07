import os
import re
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AITestGenerator:
    """Handles AI-powered test generation using OpenAI API"""
    
    def __init__(self):
        """Initialize the OpenAI client"""
        self.use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        logger.info(f"Initializing AI Generator...")
        logger.info(f"USE_OLLAMA: {self.use_ollama}")
        
        if not self.use_ollama:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            
            if not api_key or api_key == "your_openai_api_key_here":
                raise ValueError("OpenAI API key not set. Please check your .env file.")
            
            try:
                # Try importing OpenAI v1.x
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.api_version = "v1"
                logger.info("✅ OpenAI client initialized successfully (v1.x)")
            except ImportError:
                # Fall back to v0.x
                try:
                    import openai
                    openai.api_key = api_key
                    self.client = openai
                    self.api_version = "v0"
                    logger.info("✅ OpenAI client initialized successfully (v0.x)")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize OpenAI: {e}")
                    raise
        else:
            logger.info("Using Ollama mode")

    def generate_tests(self, language, code, requirements=""):
        """Generate tests for the given code and language"""
        prompt = self._build_prompt(language, code, requirements)
        
        if self.use_ollama:
            response = self._call_ollama(prompt)
        else:
            response = self._call_openai(prompt)
            
        return self._clean_response(response)

    def _call_openai(self, prompt):
        """Call OpenAI API for test generation"""
        try:
            logger.info(f"Calling OpenAI API with model: {self.openai_model}")
            
            if self.api_version == "v1":
                # OpenAI v1.x
                response = self.client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a senior QA Engineer. Return only runnable unit test code."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                return response.choices[0].message.content or ""
            else:
                # OpenAI v0.x
                response = self.client.ChatCompletion.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a senior QA Engineer. Return only runnable unit test code."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                return response['choices'][0]['message']['content'] or ""
                
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {str(e)}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def _call_ollama(self, prompt):
        """Call local Ollama API for test generation"""
        import requests
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
        
        try:
            response = requests.post(
                ollama_url,
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2,
                    "max_tokens": 2000
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"❌ Ollama API error: {str(e)}")
            raise RuntimeError(f"Ollama API error: {str(e)}")

    def _build_prompt(self, language, code, requirements):
        """Build language-specific prompts"""
        config = {
            "python": {
                "framework": "pytest",
                "extra": "Import from source.py. Cover normal cases, edge cases, and errors.",
            },
            "java": {
                "framework": "JUnit 5",
                "extra": "Use org.junit.jupiter.api.Test and assertions. Do not include package declarations.",
            },
            "javascript": {
                "framework": "Jest",
                "extra": "Use CommonJS require('./code') unless the source clearly exports differently.",
            },
        }
        details = config.get(language, config["python"])
        requirements_text = requirements.strip() or "Infer expected behavior from the code."

        return f"""Generate comprehensive {details["framework"]} unit tests for this {language} code.

Requirements:
{requirements_text}

Rules:
- Return ONLY the test code, no explanations or markdown formatting.
- Make the tests runnable as a standalone test file.
- Include all necessary imports.
- Add comments to explain each test scenario.
- {details["extra"]}

Source code:
```{language}
{code}
```"""