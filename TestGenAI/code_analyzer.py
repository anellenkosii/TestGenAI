import re
import logging

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    def __init__(self):
        self.patterns = {
            "error_handling": r"(try|except|raise|throw|ValueError|IllegalArgumentException)",
            "assertions": r"(assert|assertEquals|assertTrue|expect|should)",
            "edge_cases": r"(zero|empty|null|invalid|boundary|edge|negative)",
            "type_hints": r":\s*(int|str|float|bool|List|Dict|Optional)",
            "docstrings": r'("""|\'\'\'|/\*\*|@param)'
        }

    def analyze(self, code, language, description=""):
        analysis = {
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "test_coverage": {"happy_path": False, "edge_cases": False, "error_handling": False},
            "quality_score": 0,
            "readings": []
        }
        if "return" in code and "assert" not in code:
            analysis["weaknesses"].append("No assertions found - code returns values but nothing is verified")
            analysis["suggestions"].append("Add test functions with assertions")
        if "except" in code or "raise" in code:
            if "test" not in code.lower() and "assert" not in code:
                analysis["weaknesses"].append("Error handling exists but no tests verify it")
                analysis["suggestions"].append("Test your error handling with assertRaises")
        if "zero" in code.lower() or "null" in code.lower():
            analysis["test_coverage"]["edge_cases"] = True
            analysis["strengths"].append("Edge case handling detected")
        if "try" in code or "except" in code:
            analysis["test_coverage"]["error_handling"] = True
            analysis["strengths"].append("Error handling implemented")
        if "return" in code:
            analysis["test_coverage"]["happy_path"] = True
        score = 0
        if analysis["test_coverage"]["happy_path"]:
            score += 30
        if analysis["test_coverage"]["edge_cases"]:
            score += 30
        if analysis["test_coverage"]["error_handling"]:
            score += 30
        if len(analysis["strengths"]) > 2:
            score += 10
        analysis["quality_score"] = min(score, 100)
        if analysis["quality_score"] < 40:
            analysis["readings"] = [
                "Introduction to Unit Testing: [Link]",
                "Why Edge Cases Matter: [Link]"
            ]
        elif analysis["quality_score"] < 70:
            analysis["readings"] = [
                "Advanced Testing Strategies: [Link]",
                "Test-Driven Development Guide: [Link]"
            ]
        else:
            analysis["readings"] = [
                "Testing in Production: [Link]",
                "Mutation Testing: [Link]"
            ]
        return analysis