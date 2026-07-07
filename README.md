# 🧪 TestGen AI

> AI-Powered Unit Test Generator for Python, Java, and JavaScript

![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-API-orange.svg)
![Ollama](https://img.shields.io/badge/Ollama-Support-purple.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## 📋 Overview

**TestGen AI** is a web application that uses artificial intelligence to automatically generate unit tests for your code. Simply paste your code or upload a file, specify your requirements, and let AI generate comprehensive tests in seconds.

### 🎯 Target Users

- **Software Students** - Learn testing best practices through examples
- **Junior QA Engineers** - Accelerate test writing and improve coverage
- **Developers** - Save time on boilerplate test code

### ✨ Features

- 🤖 **AI-Powered Generation** - Uses OpenAI GPT-4o or local Ollama
- 🔧 **Multi-Language Support** - Python (pytest), Java (JUnit 5), JavaScript (Jest)
- 📝 **Multiple Input Options** - Paste code or upload files (.py, .java, .js)
- 🎨 **Syntax Highlighting** - Beautiful code display with Prism.js
- 📋 **Copy & Download** - Easy test extraction to clipboard or file
- ▶️ **Run Tests In-Browser** - Execute tests and see results instantly
- ⚡ **Real-time Feedback** - See test pass/fail outputs immediately
- 🛡️ **Secure Execution** - Tests run in isolated environments
- 🔄 **Flexible AI** - Choose between OpenAI (cloud) or Ollama (local)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key **or** Ollama (local)
- Node.js and npm (for JavaScript testing)
- Java JDK 17+ (for Java testing)

### Installation

# Clone the repository
git clone https://github.com/anellenkosii/TestGenAI.git
cd TestGenAI

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys


Running the Application
bash

# Run the Flask app
python3 app.py

# Open in browser
# http://localhost:5002

Configuration
Option 1: Using OpenAI (Cloud)
env

# .env file
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
USE_OLLAMA=false
PORT=5002

Get your API key from: OpenAI Platform
Option 2: Using Ollama (Local, Free)
env

# .env file
USE_OLLAMA=true
OLLAMA_MODEL=llama3.1
OLLAMA_API_URL=http://localhost:11434/api/generate
PORT=5002

Install Ollama:
bash

curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1
ollama serve

Java Testing (Optional)

For Java test execution, download JUnit JAR:
bash

# Download JUnit Console Standalone
wget -O junit-platform-console-standalone-1.10.2.jar \
  https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar

# Set path in .env
JUNIT_JAR=/path/to/junit-platform-console-standalone-1.10.2.jar

📁 Project Structure
text

TestGenAI/
├── app.py              # Main Flask application
├── ai_generator.py     # AI test generation logic
├── test_runner.py      # Test execution engine
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (gitignored)
├── .env.example       # Example environment configuration
├── uploads/           # Temporary upload directory
├── generated_tests/   # Generated test files
├── templates/
│   └── index.html     # Main user interface
├── static/
│   └── style.css      # Application styling
├── examples/          # Example code files
│   ├── example_python.py
│   ├── example_java.java
│   └── example_javascript.js
├── Dockerfile         # Docker container configuration
├── docker-compose.yml # Docker Compose setup
├── LICENSE            # MIT License
└── README.md          # This file

🛠️ Tech Stack
Backend

    Framework: Flask 2.3.3

    AI: OpenAI API / Ollama

    Test Runners: pytest, JUnit 5, Jest

    Python: 3.11+

Frontend

    HTML5/CSS3 - Responsive design

    Vanilla JavaScript - No frameworks needed

    Prism.js - Syntax highlighting

📝 Usage Guide
1. Select Language

Choose your programming language from the dropdown:

    Python (pytest)

    Java (JUnit 5)

    JavaScript (Jest)

2. Provide Code

Either:

    Paste code directly in the text area

    Upload a file (.py, .java, .js)

3. Add Requirements (Optional)

Describe what the code should do. Example:
text

The add function should add two numbers.
The divide function should handle division by zero.

4. Generate Tests

Click "Generate Tests" and wait for the AI to create comprehensive unit tests.
5. Review & Export

    View generated tests with syntax highlighting

    Copy to clipboard

    Download as a file

    Run tests and see results

📝 Example
Input Code (Python)
python

def add(a, b):
    """Add two numbers together"""
    return a + b

def divide(a, b):
    """Divide a by b, handling division by zero"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

Generated Tests
python

import pytest
from source import add, divide

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(5, 0) == 5

def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)

🐛 Error Handling

TestGen AI handles various error scenarios gracefully:
Error Type	Response
Missing API Key	"AI Generator not initialized"
Invalid Code	Clear error message with context
Test Failure	Detailed failure output
Network Issues	Connection error with retry suggestion
File Upload Error	Supported file types notification
🔒 Security

    Isolated Execution: Tests run in temporary directories

    Input Validation: Secure file handling with Werkzeug

    Path Sanitization: Prevention of directory traversal attacks

    No Direct Execution: User code is never executed directly

    API Key Protection: Keys stored in .env (gitignored)

🤝 Contributing

Contributions are welcome! Please follow these steps:

    Fork the repository

    Create a feature branch (git checkout -b feature/AmazingFeature)

    Commit your changes (git commit -m 'Add AmazingFeature')

    Push to the branch (git push origin feature/AmazingFeature)

    Open a Pull Request

Guidelines

    Follow PEP 8 for Python code

    Add comments for complex logic

    Update README for new features

    Write clear commit messages

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgments

    OpenAI - For the GPT API

    Ollama - For local AI capabilities

    Flask - Web framework

    Prism.js - Syntax highlighting

    pytest - Python testing framework

    JUnit 5 - Java testing framework

    Jest - JavaScript testing framework

📞 Support

    Issues: GitHub Issues

    Documentation: This README

⭐ Show Your Support

If you find TestGen AI useful, please give it a ⭐ on GitHub!

Made with ❤️ for developers who want to write better tests faster.
text


---

## 📋 Quick Checklist Before Pushing

- [ ] README.md is saved
- [ ] .env.example exists (with no real API keys)
- [ ] LICENSE file exists (MIT)
- [ ] .gitignore includes .env
- [ ] All code files are in the right places

## 🚀 Push Your Changes

```bash
# Add README if you updated it
git add README.md

# Commit
git commit -m "Update README with comprehensive documentation"

# Push
git push origin main
