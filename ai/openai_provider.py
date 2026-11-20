import os
import json
import requests
from typing import Generator, Optional
from ai.base import AIProvider

class OpenAICompatibleProvider(AIProvider):
    """Generic OpenAI-compatible provider (OpenAI, Groq, OpenRouter, etc.)."""

    def __init__(
        self,
        name: str = "openai",
        default_model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        api_key_env: str = "OPENAI_API_KEY",
        api_key: Optional[str] = None
    ):
        super().__init__(name=name, default_model=default_model)
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self._explicit_key = api_key

    def get_api_key(self) -> Optional[str]:
        return self._explicit_key or os.getenv(self.api_key_env)

    def is_available(self) -> bool:
        key = self.get_api_key()
        return bool(key and len(key.strip()) > 5)

    def list_models(self) -> list[str]:
        key = self.get_api_key()
        if not key:
            return [self.default_model]
        try:
            headers = {"Authorization": f"Bearer {key}"}
            res = requests.get(f"{self.base_url}/models", headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return [m["id"] for m in data.get("data", []) if "id" in m][:25]
        except Exception:
            pass
        return [self.default_model]

    def generate(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.5,
        max_tokens: int = 512
    ) -> str | Generator[str, None, None]:
        key = self.get_api_key()
        if not key:
            err = f"API Key not found for {self.name}. Please set {self.api_key_env} in environment variables or settings."
            if stream:
                def _err_gen():
                    yield err
                return _err_gen()
            return err

        target_model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        if stream:
            def _stream_gen():
                try:
                    with requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, stream=True, timeout=60) as resp:
                        if resp.status_code != 200:
                            yield f"[{self.name} Error {resp.status_code}: {resp.text}]"
                            return
                        for line in resp.iter_lines():
                            if not line:
                                continue
                            line_str = line.decode("utf-8")
                            if line_str.startswith("data: "):
                                data_str = line_str[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    choices = chunk.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {}).get("content", "")
                                        if delta:
                                            yield delta
                                except json.JSONDecodeError:
                                    continue
                except Exception as e:
                    yield f"[{self.name} Streaming Error: {str(e)}]"
            return _stream_gen()
        else:
            try:
                res = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=60)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                return f"[{self.name} Error {res.status_code}: {res.text}]"
            except Exception as e:
                return f"[{self.name} Connection Error: {str(e)}]"
