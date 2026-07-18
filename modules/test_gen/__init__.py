from core.modules.base import BaseModule
from core.modules.registry import registry
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

TEST_FRAMEWORKS = {
    "pytest": {
        "pattern": "test_*.py",
        "location": "tests/",
        "imports": "import pytest",
        "run_command": "pytest {test_file} -v"
    },
    "unittest": {
        "pattern": "test_*.py",
        "location": "tests/",
        "imports": "import unittest",
        "run_command": "python -m unittest {test_file} -v"
    },
    "jest": {
        "pattern": "*.test.js",
        "location": "__tests__/",
        "imports": "const {{ describe, test, expect }} = require('@jest/globals');",
        "run_command": "jest {test_file}"
    }
}

class TestGenModule(BaseModule):
    @property
    def name(self) -> str:
        return "TestGen"

    @property
    def description(self) -> str:
        return "Generate unit tests for code files. Supports pytest, unittest, and Jest frameworks."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "")
        file_path = params.get("file_path", "")
        framework = params.get("framework", "pytest")
        test_style = params.get("test_style", "comprehensive")

        if not code:
            return {"error": "No code provided for test generation"}

        if framework not in TEST_FRAMEWORKS:
            return {
                "error": f"Unsupported framework: {framework}",
                "supported": list(TEST_FRAMEWORKS.keys())
            }

        try:
            detected_lang = self._detect_language(file_path, code)
            framework_config = TEST_FRAMEWORKS[framework]

            test_file_name = self._generate_test_filename(file_path, framework)
            test_file_path = self._generate_test_path(file_path, framework_config["location"])

            prompt = self._build_test_prompt(code, file_path, framework, test_style, detected_lang)

            logger.info(f"[TestGen] Generating {framework} tests for {file_path} (style={test_style})")

            return {
                "status": "success",
                "message": "Test generation prompt ready",
                "test_file_name": test_file_name,
                "test_file_path": test_file_path,
                "framework": framework,
                "framework_config": framework_config,
                "language": detected_lang,
                "test_prompt": prompt,
                "run_command": framework_config["run_command"].format(test_file=test_file_name),
                "instructions": self._generate_instructions(file_path, test_file_path, framework, test_style)
            }
        except Exception as e:
            logger.error(f"[TestGen] Failed: {type(e).__name__}: {e}")
            return {"error": f"Test generation failed: {str(e)}"}

    def _detect_language(self, file_path: str, code: str) -> str:
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            ext_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "javascript",
                ".tsx": "typescript",
                ".java": "java",
                ".c": "c",
                ".cpp": "cpp",
                ".h": "c",
                ".hpp": "cpp",
                ".go": "go",
                ".rs": "rust",
                ".rb": "ruby",
                ".cs": "csharp",
                ".php": "php",
            }
            if ext in ext_map:
                return ext_map[ext]
        if code.startswith("package ") and "func " in code:
            return "go"
        if "fn " in code and "pub " in code:
            return "rust"
        if "def " in code or "import " in code:
            return "python"
        if "function " in code or "const " in code or "let " in code:
            return "javascript"
        return "unknown"

    def _generate_test_filename(self, file_path: str, framework: str) -> str:
        if not file_path:
            return f"test_file.{ 'js' if framework == 'jest' else 'py' }"

        base = os.path.splitext(os.path.basename(file_path))[0]
        if framework == "jest":
            return f"{base}.test.js"
        return f"test_{base}.py"

    def _generate_test_path(self, file_path: str, test_location: str) -> str:
        if file_path:
            parent = os.path.dirname(file_path)
            return os.path.join(parent, test_location, self._generate_test_filename(file_path, "pytest"))
        return os.path.join(test_location, "test_file.py")

    def _build_test_prompt(self, code: str, file_path: str, framework: str, style: str, lang: str) -> str:
        framework_config = TEST_FRAMEWORKS[framework]

        style_instructions = {
            "comprehensive": "Include tests for all functions/methods, edge cases, error handling, and boundary conditions.",
            "basic": "Include tests for main functionality only.",
            "edge_cases": "Focus on edge cases, error paths, and unusual inputs.",
            "integration": "Include integration tests that test multiple components together."
        }

        return f"""Generate {style} {framework} tests for this {lang} code.

File: {file_path}

Framework: {framework}
Test file: {self._generate_test_filename(file_path, framework)}

Requirements:
- {style_instructions.get(style, style_instructions['comprehensive'])}
- Use {framework_config['imports']}
- Include descriptive test names
- Use appropriate assertions for {framework}
- Mock external dependencies
- Test both success and failure cases
- Include setup/teardown if needed

Code to test:
```{lang}
{code}
```

Generate ONLY the test file content. No explanations, no markdown formatting around the code."""

    def _generate_instructions(self, file_path: str, test_path: str, framework: str, style: str) -> str:
        framework_config = TEST_FRAMEWORKS[framework]
        return (
            f"1. Save the generated test code to: {test_path}\n"
            f"2. Install test dependencies if needed: {'pip install pytest' if framework == 'pytest' else 'npm install --save-dev jest' if framework == 'jest' else 'pip install unittest'}\n"
            f"3. Run tests: {framework_config['run_command'].format(test_file=test_path)}\n"
            f"4. Review test coverage and adjust as needed"
        )

registry.register(TestGenModule())
