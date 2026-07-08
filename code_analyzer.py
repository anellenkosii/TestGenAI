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

        score = 0
        score += 30 if analysis["test_coverage"]["happy_path"] else 0
        score += 30 if analysis["test_coverage"]["edge_cases"] else 0
        score += 30 if analysis["test_coverage"]["error_handling"] else 0
        score += 10 if description.strip() else 0
        analysis["quality_score"] = min(score, 100)

        if analysis["quality_score"] < 40:
            analysis["readings"] = ["Unit testing basics", "Writing effective assertions"]
        elif analysis["quality_score"] < 70:
            analysis["readings"] = ["Edge case testing", "Exception testing patterns"]
        else:
            analysis["readings"] = ["Branch coverage", "Mutation testing"]

        return analysis
