from core.modules.base import BaseModule
from core.modules.registry import registry
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class FileWriteModule(BaseModule):
    @property
    def name(self) -> str:
        return "FileWrite"

    @property
    def description(self) -> str:
        return "Write or update files safely within the workspace root. Supports any text-based file type."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        mode = params.get("mode", "write")
        workspace_root = params.get("workspace_root", os.getcwd())

        if not file_path:
            return {"error": "No file_path provided"}
        if content is None:
            return {"error": "No content provided"}

        try:
            safe_path = self._resolve_safe_path(file_path, workspace_root)
        except ValueError as e:
            return {"error": str(e)}

        try:
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)

            if mode == "append" and os.path.exists(safe_path):
                write_mode = "a"
                prefix = "Appended to"
            else:
                write_mode = "w"
                prefix = "Wrote" if mode == "write" else "Wrote"

            with open(safe_path, write_mode, encoding="utf-8") as f:
                f.write(content)

            file_size = os.path.getsize(safe_path)
            lines = content.count("\n") + 1

            logger.info(f"[FileWrite] {prefix} {safe_path} ({file_size} bytes, {lines} lines)")

            return {
                "status": "success",
                "message": f"{prefix} {file_path}",
                "file_path": file_path,
                "absolute_path": safe_path,
                "bytes_written": file_size,
                "lines": lines,
                "mode": mode
            }
        except Exception as e:
            logger.error(f"[FileWrite] Failed to write {file_path}: {type(e).__name__}: {e}")
            return {"error": f"Write failed: {str(e)}"}

    def _resolve_safe_path(self, file_path: str, workspace_root: str) -> str:
        workspace_root = os.path.abspath(workspace_root)

        if os.path.isabs(file_path):
            resolved = os.path.abspath(file_path)
        else:
            resolved = os.path.abspath(os.path.join(workspace_root, file_path))

        if not resolved.startswith(workspace_root + os.sep) and resolved != workspace_root:
            raise ValueError(f"Path traversal detected: {file_path} resolves outside workspace root")

        return resolved

registry.register(FileWriteModule())
