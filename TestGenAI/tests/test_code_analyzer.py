from code_analyzer import CodeAnalyzer


def test_detects_error_handling_and_edge_cases():
    analyzer = CodeAnalyzer()
    code = """
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""
    result = analyzer.analyze(code, "python")
    assert result["test_coverage"]["happy_path"] is True
    assert result["test_coverage"]["error_handling"] is True
    assert result["quality_score"] >= 60


def test_flags_missing_assertions_for_bare_return():
    analyzer = CodeAnalyzer()
    code = "def add(a, b):\n    return a + b\n"
    result = analyzer.analyze(code, "python")
    assert "No assertions found in the submitted code" in result["weaknesses"]


def test_description_bumps_score():
    analyzer = CodeAnalyzer()
    code = "def add(a, b):\n    return a + b\n"
    without_description = analyzer.analyze(code, "python")
    with_description = analyzer.analyze(code, "python", description="adds two numbers")
    assert with_description["quality_score"] > without_description["quality_score"]


def test_quality_score_never_exceeds_100():
    analyzer = CodeAnalyzer()
    code = "try:\n    x = None\n    if x is None or x == 0:\n        raise ValueError('empty')\nexcept ValueError:\n    pass\nreturn x\n"
    result = analyzer.analyze(code, "python", description="edge cases and errors")
    assert result["quality_score"] <= 100
