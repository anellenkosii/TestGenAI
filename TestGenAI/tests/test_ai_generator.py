from ai_generator import AITestGenerator


def test_build_prompt_includes_code_and_framework():
    generator = AITestGenerator()
    prompt = generator._build_prompt("python", "def add(a, b):\n    return a + b", "", tdd=False)
    assert "pytest" in prompt
    assert "def add(a, b):" in prompt


def test_build_prompt_tdd_mode_changes_instruction():
    generator = AITestGenerator()
    standard = generator._build_prompt("python", "code", "", tdd=False)
    tdd = generator._build_prompt("python", "code", "", tdd=True)
    assert "test-driven development" in tdd
    assert "test-driven development" not in standard


def test_clean_response_strips_markdown_fence():
    generator = AITestGenerator()
    raw = "```python\ndef test_a():\n    assert True\n```"
    assert generator._clean_response(raw) == "def test_a():\n    assert True"


def test_clean_response_handles_missing_fence():
    generator = AITestGenerator()
    raw = "def test_a():\n    assert True"
    assert generator._clean_response(raw) == raw


def test_explain_counts_python_tests():
    generator = AITestGenerator()
    tests = "def test_a():\n    pass\ndef test_b():\n    pass\n"
    explanation = generator._explain(tests, "python", tdd=False)
    assert "Estimated test cases: 2" in explanation
