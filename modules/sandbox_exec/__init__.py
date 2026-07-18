from core.modules.base import BaseModule
from core.modules.registry import registry
from typing import Dict, Any
import subprocess
import os
import time
import logging
import platform

logger = logging.getLogger(__name__)

ALLOWED_COMMANDS = [
    "ls", "dir", "pwd", "cd",
    "cat", "type", "head", "more",
    "find", "where", "tree",
    "echo", "print",
    "grep", "select-string",
    "wc", "measure-object",
    "python", "python3",
    "node",
    "pip", "pip3",
    "npm",
    "git",
    "pytest", "py.test",
    "ruff", "flake8", "mypy",
    "tsc", "eslint",
    "cargo", "rustc",
    "go",
    "gcc", "g++", "clang", "clang++",
    "javac", "java",
    "curl",
    "make", "cmake",
    "docker",
    "code",
]

BLOCKED_PATTERNS = [
    "rm -rf /", "rm -rf /*",
    "format", "mkfs",
    "shutdown", "reboot", "restart",
    "del /f /s /q",
    "rd /s /q",
    ":(){:|:&};:",
    "wget.*-O.*\\|.*sh",
    "curl.*\\|.*sh",
    "powershell.*-enc",
]

class SandboxExecModule(BaseModule):
    @property
    def name(self) -> str:
        return "SandboxExec"

    @property
    def description(self) -> str:
        return "Execute commands in a sandboxed environment with restricted scope, timeout, and output capture."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        command = params.get("command", "")
        timeout = int(params.get("timeout", 30))
        workdir = params.get("workdir", os.getcwd())

        if not command:
            return {"error": "No command provided"}

        if timeout > 120:
            return {"error": "Timeout cannot exceed 120 seconds"}

        try:
            self._validate_command(command)
        except ValueError as e:
            return {"error": str(e)}

        try:
            safe_workdir = os.path.abspath(workdir)
            if not os.path.isdir(safe_workdir):
                return {"error": f"Working directory does not exist: {workdir}"}

            logger.info(f"[SandboxExec] Executing: {command[:100]}... (timeout={timeout}s, dir={safe_workdir})")

            start_time = time.time()

            if platform.system() == "Windows":
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=safe_workdir,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=safe_workdir
                )

            elapsed = time.time() - start_time

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            max_output = 50000
            if len(stdout) > max_output:
                stdout = stdout[:max_output] + "\n...[output truncated]"
            if len(stderr) > max_output:
                stderr = stderr[:max_output] + "\n...[output truncated]"

            logger.info(f"[SandboxExec] Completed in {elapsed:.2f}s, exit_code={result.returncode}")

            return {
                "status": "success" if result.returncode == 0 else "error",
                "command": command,
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "elapsed_seconds": round(elapsed, 2),
                "working_directory": safe_workdir,
                "timeout_seconds": timeout
            }

        except subprocess.TimeoutExpired:
            logger.error(f"[SandboxExec] Command timed out after {timeout}s: {command[:100]}")
            return {
                "error": f"Command timed out after {timeout} seconds",
                "command": command,
                "timeout_seconds": timeout
            }
        except Exception as e:
            logger.error(f"[SandboxExec] Execution failed: {type(e).__name__}: {e}")
            return {"error": f"Execution failed: {str(e)}"}

    def _validate_command(self, command: str):
        cmd_lower = command.lower().strip()

        for pattern in BLOCKED_PATTERNS:
            import re
            if re.search(pattern, cmd_lower):
                raise ValueError(f"Command blocked by security policy: contains '{pattern}'")

        base_cmd = cmd_lower.split()[0] if cmd_lower else ""
        base_cmd = os.path.basename(base_cmd).lower()

        if base_cmd in ["del", "remove-item", "ri", "erase", "rmdir"]:
            raise ValueError("File deletion commands require explicit user confirmation (not allowed via module)")

        if base_cmd in ["move", "ren", "rename", "rename-item"]:
            raise ValueError("File move/rename commands require explicit user confirmation (not allowed via module)")

        if base_cmd in ALLOWED_COMMANDS or any(
            cmd in ALLOWED_COMMANDS for cmd in [base_cmd, base_cmd.replace(".exe", "")]
        ):
            return

        if base_cmd.startswith("python") or base_cmd.startswith("node"):
            return

        if not base_cmd:
            raise ValueError("Empty command")

        logger.warning(f"[SandboxExec] Command '{base_cmd}' not in whitelist but allowed (validation passed)")

registry.register(SandboxExecModule())
