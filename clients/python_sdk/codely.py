import requests
import os
from typing import Dict, Any, List, Optional

class CodelyClient:
    def __init__(self, base_url: str = "http://localhost:8889", session_id: str = None):
        self.base_url = f"{base_url}/api/v1"
        self.session_id = session_id or os.getenv("CODELY_SESSION_ID")
        self._session = requests.Session()
        self._set_auth_header()

    def _set_auth_header(self):
        if self.session_id:
            self._session.headers.update({"Authorization": f"Bearer {self.session_id}"})

    def set_session(self, session_id: str):
        self.session_id = session_id
        self._set_auth_header()

    def _make_request(self, method, url, **kwargs):
        response = getattr(self._session, method)(url, **kwargs)
        if response.status_code == 401:
            raise Exception("Authentication required. Use --session-id or set CODELY_SESSION_ID env var.")
        response.raise_for_status()
        return response.json()

    def chat(self, context_id: str, prompt: str, mode: str = "normal", stream: bool = False) -> Dict[str, Any]:
        url = f"{self.base_url}/chat"
        payload = {
            "context_id": context_id,
            "prompt": prompt,
            "mode": mode,
            "stream": stream
        }
        return self._make_request("post", url, json=payload)

    def add_memory(self, context_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/memory/add"
        payload = {
            "context_id": context_id,
            "text": text,
            "metadata": metadata or {}
        }
        return self._make_request("post", url, json=payload)

    def clear_memory(self, context_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/memory/clear/{context_id}"
        return self._make_request("delete", url)

    def list_modules(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/modules"
        return self._make_request("get", url).get("modules", [])

    def execute_module(self, module_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/modules/execute/{module_name}"
        return self._make_request("post", url, json=params)

    def ingest_file(self, context_id: str, file_path: str) -> Dict[str, Any]:
        url = f"{self.base_url}/ingest/file"
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"context_id": context_id}
            return self._make_request("post", url, files=files, data=data)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/tasks/{task_id}"
        return self._make_request("get", url)

    def chat_with_files(
        self,
        context_id: str,
        prompt: str,
        files: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
        save_to_memory: bool = False,
        mode: str = "normal"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat-with-files"

        form_data = {
            "context_id": context_id,
            "prompt": prompt,
            "save_to_memory": str(save_to_memory).lower(),
            "mode": mode
        }

        if urls:
            form_data["urls"] = ",".join(urls)

        file_handles = []
        try:
            files_data = []
            if files:
                for file_path in files:
                    if os.path.exists(file_path):
                        file_handles.append(open(file_path, "rb"))
                        files_data.append(("files", file_handles[-1]))
                    else:
                        print(f"Warning: File not found: {file_path}")

            return self._make_request(
                "post",
                url,
                data=form_data,
                files=files_data if files_data else None
            )
        finally:
            for f in file_handles:
                f.close()

    def list_threads(self) -> Dict[str, Any]:
        url = f"{self.base_url}/threads"
        return self._make_request("get", url)

    def get_thread_stats(self, context_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/threads/{context_id}/stats"
        return self._make_request("get", url)

    def delete_thread(self, context_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/threads/{context_id}"
        return self._make_request("delete", url)

    def merge_memory(
        self,
        target_context_id: str,
        source_context_ids: List[str]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/memory/merge"
        payload = {
            "target_context_id": target_context_id,
            "source_context_ids": source_context_ids
        }
        return self._make_request("post", url, json=payload)

    def switch_model(self, model_type: str, model_name: str) -> Dict[str, Any]:
        url = f"{self.base_url}/model/switch"
        payload = {
            "model_type": model_type,
            "model_name": model_name
        }
        return self._make_request("post", url, json=payload)

    def request_login(self, email: str, display_name: str = None) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/request-login"
        payload = {"email": email}
        if display_name:
            payload["display_name"] = display_name
        return self._make_request("post", url, json=payload)

    def verify_token(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/verify"
        payload = {"token": token}
        return self._make_request("post", url, json=payload)

    def get_user_info(self) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/me"
        return self._make_request("get", url)

    def logout(self) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/logout"
        return self._make_request("post", url)

    def login(self, email: str) -> Dict[str, Any]:
        result = self.request_login(email)
        if result.get("dev_link"):
            print(f"\nMagic link: {result['dev_link']}")
        return result

    def list_tools(self) -> Dict[str, Any]:
        url = f"{self.base_url}/tools"
        return self._make_request("get", url)

    def write_file(self, file_path: str, content: str, mode: str = "write") -> Dict[str, Any]:
        url = f"{self.base_url}/tools/write-file"
        payload = {
            "file_path": file_path,
            "content": content,
            "mode": mode
        }
        return self._make_request("post", url, json=payload)

    def exec_command(self, command: str, timeout: int = 30, workdir: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/tools/exec-command"
        payload = {
            "command": command,
            "timeout": timeout,
            "workdir": workdir
        }
        return self._make_request("post", url, json=payload)

    def generate_tests(
        self,
        code: str,
        file_path: Optional[str] = None,
        framework: str = "pytest",
        test_style: str = "comprehensive"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/tools/generate-tests"
        payload = {
            "code": code,
            "file_path": file_path,
            "framework": framework,
            "test_style": test_style
        }
        return self._make_request("post", url, json=payload)
