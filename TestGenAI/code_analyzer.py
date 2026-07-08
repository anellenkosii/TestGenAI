import re

class CodeAnalyzer:
    def analyze(self, code, language, description=""):
        analysis = {
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "test_coverage": {"happy_path": False, "edge_cases": False, "error_handling": False},
            "quality_score": 0,
            "readings": [],
        }
        lower = code.lower()
        if "return" in code:
            analysis["test_coverage"]["happy_path"] = True
        if re.search(r"\b(zero|empty|null|none|invalid|negative|boundary)\b", lower):
            analysis["test_coverage"]["edge_cases"] = True
            analysis["strengths"].append("Edge case handling detected")
        if re.search(r"\b(try|except|raise|throw|valueerror|illegalargumentexception)\b", lower):
            analysis["test_coverage"]["error_handling"] = True
            analysis["strengths"].append("Error handling detected")
        if "return" in code and "assert" not in lower and "expect" not in lower:
            analysis["weaknesses"].append("No assertions found in the submitted code")
            analysis["suggestions"].append("Generate tests that assert returned values and side effects")
        if description.strip():
            analysis["strengths"].append("Requirements context provided")
        if language == "python" and "def " in code and ":" not in code:
            analysis["suggestions"].append("Check Python syntax before generating tests")
        if language == "java" and "public class" not in code:
            analysis["suggestions"].append("Java code should have a public class definition")
        if language == "javascript" and "module.exports" not in code and "export" not in code:
            analysis["suggestions"].append("JavaScript code should export functions for testing")
        score = 0
        score += 30 if analysis["test_coverage"]["happy_path"] else 0
        score += 30 if analysis["test_coverage"]["edge_cases"] else 0
        score += 30 if analysis["test_coverage"]["error_handling"] else 0
        score += 10 if description.strip() else 0
        analysis["quality_score"] = min(score, 100)
        if analysis["quality_score"] < 40:
            analysis["readings"] = [
                "Unit testing basics: https://www.guru99.com/unit-testing-guide.html",
                "Writing effective assertions: https://docs.pytest.org/en/stable/assert.html"
            ]
        elif analysis["quality_score"] < 70:
            analysis["readings"] = [
                "Edge case testing: https://www.softwaretestinghelp.com/edge-testing/",
                "Exception testing patterns: https://www.baeldung.com/junit-assert-exception"
            ]
        else:
            analysis["readings"] = [
                "Branch coverage: https://www.atlassian.com/continuous-delivery/software-testing/code-coverage",
                "Mutation testing: https://www.softwaretestinghelp.com/mutation-testing/"
            ]
        return analysis