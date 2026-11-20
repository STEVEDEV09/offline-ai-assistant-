import os
import json
import requests
from typing import Generator, Optional
from ai.base import AIProvider

class GeminiProvider(AIProvider):
    """Google Gemini AI Provider using REST API."""

    def __init__(
        self,
        default_model: str = "gemini-1.5-flash",
        api_key_env: str = "GEMINI_API_KEY",
        api_key: Optional[str] = None
    ):
        super().__init__(name="gemini", default_model=default_model)
        self.api_key_env = api_key_env
        self._explicit_key = api_key

    def get_api_key(self) -> Optional[str]:
        return self._explicit_key or os.getenv(self.api_key_env)

    def is_available(self) -> bool:
        key = self.get_api_key()
        return bool(key and len(key.strip()) > 5)

    def list_models(self) -> list[str]:
        return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]

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
            err = f"API Key not found for Gemini. Set {self.api_key_env} in environment or config."
            if stream:
                def _err_gen():
                    yield err
                return _err_gen()
            return err

        target_model = model or self.default_model

        # Convert messages to Gemini contents format
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={key}"

        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text = parts[0].get("text", "")
                        if stream:
                            def _gen():
                                yield text
                            return _gen()
                        return text.strip()
                return "Gemini returned an empty response."
            else:
                err_text = f"Gemini API Error {res.status_code}: {res.text}"
                if stream:
                    def _err_gen2():
                        yield err_text
                    return _err_gen2()
                return err_text
        except Exception as e:
            err_text = f"Gemini Connection Error: {str(e)}"
            if stream:
                def _err_gen3():
                    yield err_text
                return _err_gen3()
            return err_text
