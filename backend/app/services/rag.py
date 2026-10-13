from uuid import uuid4
import logging

import chromadb

from app.core.config import get_settings
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)

DEFAULT_ACADEMIC_CHUNKS = [
    {
        "text": "Academic Thesis Standard Structure: Each chapter must open with a comprehensive conceptual foundation, followed by formal technical breakdown, architectural illustrations, equations or schema representations where applicable, and close with a summary bridging into the subsequent chapter.",
        "metadata": {"college": "University Standard", "branch": "Engineering & Technology", "topic": "Report Organization"},
    },
    {
        "text": "Literature Survey & Theoretical Background: Review state-of-the-art literature, comparative analysis table benchmarking existing research against proposed methodology, highlighting architectural gaps and technical motivations.",
        "metadata": {"college": "University Standard", "branch": "Computer Science / IT", "topic": "Literature Review"},
    },
    {
        "text": "System Architecture & Database Specifications: Detail formal multi-tier architecture, Entity-Relationship (ER) model with 3NF normalization, RESTful API endpoints, request/response payloads, and security boundaries.",
        "metadata": {"college": "University Standard", "branch": "Computer Science / IT", "topic": "System Design"},
    },
    {
        "text": "Implementation & Core Algorithms: Concrete walkthrough of primary modules, algorithmic pseudo-code, mathematical formulation, framework integration details, hardware/software stack parameters, and development workflow.",
        "metadata": {"college": "University Standard", "branch": "Engineering & Technology", "topic": "Implementation"},
    },
    {
        "text": "Testing Strategy & Quality Assurance: Comprehensive test case matrices with Test Case ID, Description, Input Values, Expected Output, Actual Output, and Verification status across Unit, Integration, and System Testing.",
        "metadata": {"college": "University Standard", "branch": "Computer Science / IT", "topic": "Quality Assurance & Testing"},
    },
    {
        "text": "Results Analysis & IEEE Conclusion: Empirical metrics, performance comparison graphs, system throughput, loss/accuracy curves, limitations, real-world deployment viability, and future research scope.",
        "metadata": {"college": "University Standard", "branch": "Engineering & Technology", "topic": "Results & Conclusion"},
    },
]


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
        try:
            if self.collection.count() == 0:
                # Seed default curriculum chunks so knowledge base is immediately rich
                try:
                    self.add_document(
                        [item["text"] for item in DEFAULT_ACADEMIC_CHUNKS],
                        {"college": "University Standard", "branch": "Engineering", "source": "core_curriculum"},
                    )
                except Exception as seed_err:
                    logger.debug("Automatic RAG seed skipped: %s", seed_err)

            if self.collection.count() > 0:
                embeddings = self.ai.embed([query])
                result = self.collection.query(
                    query_embeddings=embeddings,
                    n_results=min(n_results * 3, self.collection.count()),
                )
                docs = result.get("documents", [[]])[0]
                metadatas = result.get("metadatas", [[]])[0]
                distances = result.get("distances", [[]])[0]
                chunks = [
                    {"text": doc, "metadata": meta, "distance": distance}
                    for doc, meta, distance in zip(docs, metadatas, distances)
                ]
                if chunks:
                    return self._rank_by_metadata(chunks, metadata_hint or {})[:n_results]
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s. Using default academic framework.", exc)

        return self._rank_by_metadata(DEFAULT_ACADEMIC_CHUNKS, metadata_hint or {})[:n_results]

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
