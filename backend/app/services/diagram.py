import base64
import io
import logging
import requests
from PIL import Image, ImageDraw

from app.core.config import get_settings
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class DiagramRenderer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage = StorageService()

    def _render_external(self, definition: str) -> bytes | None:
        endpoints = []
        if self.settings.kroki_url:
            endpoints.append(f"{self.settings.kroki_url.rstrip('/')}/mermaid/png")
        # kroki.io is fast and reliable for rendering Mermaid to PNG
        endpoints.append("https://kroki.io/mermaid/png")

        for endpoint in endpoints:
            try:
                res = requests.post(
                    endpoint,
                    data=definition.encode("utf-8"),
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                    timeout=8,
                )
                if res.status_code == 200 and res.content.startswith(b"\x89PNG"):
                    return res.content
            except Exception as e:
                logger.debug("Kroki endpoint %s failed: %s", endpoint, e)

        # Secondary fallback: mermaid.ink with a short timeout
        try:
            encoded = base64.urlsafe_b64encode(definition.encode("utf-8")).decode("ascii")
            res = requests.get(f"https://mermaid.ink/img/{encoded}", timeout=6)
            if res.status_code == 200 and res.content.startswith(b"\x89PNG"):
                return res.content
        except Exception as e:
            logger.debug("mermaid.ink failed: %s", e)

        return None

    def _render_fallback_card(self, title: str, definition: str) -> bytes:
        """Create a clean, publication-ready diagram blueprint card when external renderers are unreachable."""
        width, height = 900, 420
        img = Image.new("RGB", (width, height), color=(248, 250, 252))
        draw = ImageDraw.Draw(img)

        # Outer notebook-style border
        draw.rectangle([8, 8, width - 8, height - 8], outline=(30, 64, 175), width=2)
        # Header banner
        draw.rectangle([8, 8, width - 8, 55], fill=(30, 64, 175))
        draw.text((25, 20), f"SYSTEM BLUEPRINT: {title.upper()}", fill=(255, 255, 255))

        # Content lines extracted from mermaid nodes
        lines = [
            line.strip()
            for line in definition.split("\n")
            if line.strip() and not line.strip().startswith("%%")
        ][:12]

        y = 75
        draw.text((25, y), "Architecture Specification & Logic Flow:", fill=(71, 85, 105))
        y += 26
        for line in lines:
            draw.text((35, y), f"• {line[:85]}", fill=(15, 23, 42))
            y += 22

        # Footer watermark
        draw.text(
            (25, height - 30),
            "Draftly Academic Studio • Auto-compiled Architectural Schematic",
            fill=(148, 163, 184),
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def render_mermaid_png(self, title: str, definition: str) -> dict:
        content = None
        try:
            content = self._render_external(definition)
        except Exception as exc:
            logger.warning("External diagram renderers threw error for '%s': %s", title, exc)

        if not content:
            logger.info("Using local fallback card for diagram: %s", title)
            content = self._render_fallback_card(title, definition)

        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title).strip("_") or "diagram"
        key, size = self.storage.write_bytes(content, "generated/diagrams", f"{safe_title}.png")
        return {
            "title": title,
            "type": "mermaid",
            "definition": definition,
            "storage_key": key,
            "size_bytes": size,
        }

    def render_many(self, diagrams: list[dict]) -> list[dict]:
        rendered: list[dict] = []
        for diagram in diagrams:
            if diagram.get("type") == "mermaid":
                try:
                    title = diagram.get("title") or "System Diagram"
                    definition = diagram.get("definition") or "graph TD\n  Start --> End"
                    rendered.append(self.render_mermaid_png(title, definition))
                except Exception as exc:
                    logger.warning("Diagram '%s' could not be rendered: %s", diagram.get("title"), exc)
        return rendered
