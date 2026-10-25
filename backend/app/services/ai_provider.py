import json
import time
from abc import ABC, abstractmethod
from http.client import RemoteDisconnected
from socket import gaierror

from google import genai
from google.genai.errors import APIError, ServerError
from requests import RequestException

from app.core.config import get_settings


class AIProvider(ABC):
    @abstractmethod
    def generate_json(self, prompt: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def describe_image(self, image_bytes: bytes, mime_type: str = "image/png", prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for AI generation and embeddings")
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate_text(self, prompt: str) -> str:
        last_error: Exception | None = None
        for model in self.settings.generation_models:
            for attempt in range(self.settings.gemini_max_retries + 1):
                try:
                    response = self.client.models.generate_content(model=model, contents=prompt)
                    return response.text or ""
                except (APIError, ServerError) as exc:
                    last_error = exc
                    if not self._should_retry(exc) or attempt == self.settings.gemini_max_retries:
                        break
                    time.sleep(self.settings.gemini_retry_delay_seconds * (attempt + 1))
        detail = str(last_error) if last_error else "unknown error"
        models = ", ".join(self.settings.generation_models)
        raise RuntimeError(f"Gemini generation failed after trying {models}: {detail}") from last_error

    def generate_json(self, prompt: str) -> dict:
        text = self.generate_text(
            prompt
            + "\nReturn strict JSON only. Do not wrap it in markdown fences or add commentary."
        ).strip()
        import re

        cleaned = text
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1]
            if "```" in cleaned:
                cleaned = cleaned.split("```", 1)[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1]
            if "```" in cleaned:
                cleaned = cleaned.split("```", 1)[0]

        cleaned = cleaned.strip()
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            repaired = re.sub(r",\s*([\]\}])", r"\1", cleaned)
            open_braces = repaired.count("{") - repaired.count("}")
            open_brackets = repaired.count("[") - repaired.count("]")
            repaired += ("]" * max(0, open_brackets)) + ("}" * max(0, open_braces))
            return json.loads(repaired)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            result = self._embed_with_retry(text)
            vectors.append(result.embeddings[0].values)
        return vectors

    def describe_image(self, image_bytes: bytes, mime_type: str = "image/png", prompt: str = "") -> str:
        from google.genai import types

        instruction = prompt or (
            "Analyze this uploaded project attachment image (which may be a technical diagram, "
            "CAD / architectural drawing, site photograph, laboratory test graph, structural model, "
            "schematic circuit, calculation sheet, survey chart, or software UI). "
            "1. Identify the academic discipline/domain (e.g. Civil Engineering, Mechanical, Electrical, Computer Science, Management, etc.). "
            "2. Extract ALL readable text, axis metrics, table values, equations, labels, and component names. "
            "3. Detail the technical workflow, structural elements, process steps, or physical setup shown. "
            "4. Summarize the key empirical findings, test results, or design parameters so they can be cited in a formal academic project report."
        )
        try:
            part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        except Exception:
            return "Image exhibit provided as project empirical documentation."

        last_error: Exception | None = None
        for model in self.settings.generation_models:
            for attempt in range(self.settings.gemini_max_retries + 1):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[instruction, part],
                    )
                    return response.text or ""
                except (APIError, ServerError) as exc:
                    last_error = exc
                    if not self._should_retry(exc) or attempt == self.settings.gemini_max_retries:
                        break
                    time.sleep(self.settings.gemini_retry_delay_seconds * (attempt + 1))
                except Exception as exc:
                    last_error = exc
                    break
        return "Image exhibit provided as project empirical documentation."

    def _embed_with_retry(self, text: str):
        last_error: Exception | None = None
        for attempt in range(self.settings.gemini_max_retries + 1):
            try:
                return self.client.models.embed_content(
                    model=self.settings.gemini_embedding_model,
                    contents=text[:8000],
                )
            except (APIError, ServerError, RequestException, OSError, RemoteDisconnected, gaierror) as exc:
                last_error = exc
                if isinstance(exc, (APIError, ServerError)) and not self._should_retry(exc):
                    break
                if attempt == self.settings.gemini_max_retries:
                    break
                time.sleep(self.settings.gemini_retry_delay_seconds * (attempt + 1))
        detail = str(last_error) if last_error else "unknown error"
        raise RuntimeError(
            "Gemini embedding failed. Check internet/DNS access to generativelanguage.googleapis.com "
            f"and verify GEMINI_API_KEY. Detail: {detail}"
        ) from last_error

    def _should_retry(self, exc: Exception) -> bool:
        code = getattr(exc, "code", None)
        status = str(getattr(exc, "status", "") or "").upper()
        message = str(exc).lower()
        return code in {429, 500, 502, 503, 504} or status in {"RESOURCE_EXHAUSTED", "UNAVAILABLE", "INTERNAL"} or "high demand" in message


def get_ai_provider() -> AIProvider:
    return GeminiProvider()
