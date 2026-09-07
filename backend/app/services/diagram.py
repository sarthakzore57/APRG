import base64
import requests

from app.core.config import get_settings
from app.services.storage import StorageService


class DiagramRenderer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = StorageService()

    def render_mermaid_png(self, title: str, definition: str) -> dict:
        encoded = base64.urlsafe_b64encode(definition.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}"
        if self.settings.kroki_url:
            response = requests.post(
                f"{self.settings.kroki_url.rstrip('/')}/mermaid/png",
                data=definition.encode("utf-8"),
                timeout=20,
            )
        else:
            response = requests.get(url, timeout=20)
        response.raise_for_status()
        key, size = self.storage.write_bytes(response.content, "generated/diagrams", f"{title}.png")
        return {"title": title, "type": "mermaid", "definition": definition, "storage_key": key, "size_bytes": size}

    def render_many(self, diagrams: list[dict]) -> list[dict]:
        rendered: list[dict] = []
        for diagram in diagrams:
            if diagram.get("type") == "mermaid":
                rendered.append(self.render_mermaid_png(diagram["title"], diagram["definition"]))
        return rendered
