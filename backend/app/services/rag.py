from uuid import uuid4

import chromadb

from app.core.config import get_settings
from app.services.ai_provider import AIProvider


class RagService:
    def __init__(self, ai: AIProvider) -> None:
        self.ai = ai
        self.client = chromadb.PersistentClient(path=get_settings().chroma_path)
        self.collection = self.client.get_or_create_collection("academic_reports")

    def add_document(self, chunks: list[str], metadata: dict) -> int:
        if not chunks:
            return 0
        embeddings = self.ai.embed(chunks)
        ids = [uuid4().hex for _ in chunks]
        metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)
        return len(chunks)

    def retrieve(self, query: str, n_results: int = 6, metadata_hint: dict | None = None) -> list[dict]:
        if self.collection.count() == 0:
            return []
        embeddings = self.ai.embed([query])
        result = self.collection.query(query_embeddings=embeddings, n_results=min(n_results * 3, self.collection.count()))
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        chunks = [
            {"text": doc, "metadata": meta, "distance": distance}
            for doc, meta, distance in zip(docs, metadatas, distances)
        ]
        return self._rank_by_metadata(chunks, metadata_hint or {})[:n_results]

    def _rank_by_metadata(self, chunks: list[dict], hint: dict) -> list[dict]:
        def normalize(value: object) -> str:
            return str(value or "").strip().lower()

        hint_terms = {
            "college": normalize(hint.get("college")),
            "branch": normalize(hint.get("branch")),
            "technology": normalize(hint.get("technology")),
        }
        technologies = [term.strip() for term in hint_terms["technology"].replace("\n", ",").replace(";", ",").split(",") if term.strip()]

        def score(chunk: dict) -> tuple[int, float]:
            metadata = chunk.get("metadata") or {}
            value_score = 0
            if hint_terms["college"] and hint_terms["college"] == normalize(metadata.get("college")):
                value_score += 3
            if hint_terms["branch"] and hint_terms["branch"] == normalize(metadata.get("branch")):
                value_score += 3
            metadata_technology = normalize(metadata.get("technology"))
            if metadata_technology and any(term in metadata_technology or metadata_technology in term for term in technologies):
                value_score += 2
            return value_score, -float(chunk.get("distance") or 0)

        return sorted(chunks, key=score, reverse=True)
