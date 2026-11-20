import urllib.request
import json
from typing import Generator, Optional
from ai.base import AIProvider

class OllamaProvider(AIProvider):
    """Local Ollama AI Provider."""

    def __init__(self, host: str = "http://localhost:11434", default_model: str = "tinyllama"):
        super().__init__(name="ollama", default_model=default_model)
        self.host = host.rstrip("/")

    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "JarvisAI"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            import ollama
            res = ollama.list()
            model_list = getattr(res, "models", res)
            models = []
            for item in model_list:
                if hasattr(item, "model"):
                    models.append(item.model)
                elif isinstance(item, dict):
                    models.append(item.get("name") or item.get("model", "unknown"))
            return models if models else [self.default_model]
        except Exception:
            return [self.default_model]

    def generate(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.5,
        max_tokens: int = 512
    ) -> str | Generator[str, None, None]:
        import ollama
        target_model = model or self.default_model

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "top_p": 0.9
        }

        if stream:
            def _stream_gen():
                try:
                    stream_resp = ollama.chat(
                        model=target_model,
                        messages=messages,
                        stream=True,
                        options=options,
                        keep_alive="60m"
                    )
                    for chunk in stream_resp:
                        delta = chunk.get("message", {}).get("content", "")
                        if delta:
                            yield delta
                except Exception as e:
                    yield f"\n[Ollama Streaming Error: {str(e)}]"
            return _stream_gen()
        else:
            try:
                resp = ollama.chat(
                    model=target_model,
                    messages=messages,
                    stream=False,
                    options=options,
                    keep_alive="60m"
                )
                return resp.get("message", {}).get("content", "").strip()
            except Exception as e:
                return f"Ollama Error: {str(e)}. Make sure Ollama is running ('ollama serve')."
