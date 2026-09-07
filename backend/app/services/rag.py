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

    def retrieve(self, query: str, n_results: int = 6) -> list[dict]:
        embeddings = self.ai.embed([query])
        result = self.collection.query(query_embeddings=embeddings, n_results=n_results)
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {"text": doc, "metadata": meta, "distance": distance}
            for doc, meta, distance in zip(docs, metadatas, distances)
        ]
