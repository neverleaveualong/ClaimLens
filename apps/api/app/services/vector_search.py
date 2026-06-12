from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pinecone import Pinecone, ServerlessSpec
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.patent import Claim, ClaimElement, Patent
from app.services.embedding_client import OpenAIEmbeddingClient


EMBEDDING_DIMENSION = 1536
TEXT_TYPE_PATENT_ABSTRACT = "patent_abstract"
TEXT_TYPE_INDEPENDENT_CLAIM = "independent_claim"
TEXT_TYPE_CLAIM_ELEMENT = "claim_element"


@dataclass(frozen=True)
class ClaimVectorDocument:
    id: str
    text: str
    metadata: dict[str, str | int | float | bool]


@dataclass(frozen=True)
class VectorSearchResult:
    id: str
    score: float
    text: str
    metadata: dict[str, Any]


class PineconeClaimVectorIndex:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        index_name: str | None = None,
        namespace: str | None = None,
        embedding_client: OpenAIEmbeddingClient | None = None,
        pinecone_client: Pinecone | None = None,
        index: Any | None = None,
    ) -> None:
        resolved_api_key = api_key or settings.pinecone_api_key
        if not resolved_api_key and pinecone_client is None and index is None:
            raise ValueError("PINECONE_API_KEY is missing.")

        self.index_name = index_name or settings.pinecone_index_name
        self.namespace = namespace if namespace is not None else settings.pinecone_namespace
        self.embedding_client = embedding_client or OpenAIEmbeddingClient()
        self.pinecone = pinecone_client or (
            None if index is not None else Pinecone(api_key=resolved_api_key)
        )
        self._index = index

    @property
    def index(self) -> Any:
        if self._index is None:
            if self.pinecone is None:
                raise ValueError("Pinecone client is missing.")
            self._index = self.pinecone.Index(self.index_name)
        return self._index

    def ensure_index(self, dimension: int = EMBEDDING_DIMENSION) -> None:
        if self.pinecone is None:
            raise ValueError("Pinecone client is missing.")
        index_names = _pinecone_index_names(self.pinecone.list_indexes())
        if self.index_name in index_names:
            return

        self.pinecone.create_index(
            name=self.index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud,
                region=settings.pinecone_region,
            ),
        )
        while self.index_name not in _pinecone_index_names(self.pinecone.list_indexes()):
            time.sleep(1)

    def clear_namespace(self) -> None:
        try:
            self.index.delete(delete_all=True, namespace=self.namespace)
        except Exception as exc:
            if "Namespace not found" not in str(exc):
                raise

    def upsert_documents(
        self,
        documents: Sequence[ClaimVectorDocument],
        batch_size: int = 50,
    ) -> int:
        saved = 0
        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            embeddings = self.embedding_client.embed_texts([document.text for document in batch])
            vectors = [
                {
                    "id": document.id,
                    "values": embedding,
                    "metadata": {
                        **document.metadata,
                        "text": document.text,
                    },
                }
                for document, embedding in zip(batch, embeddings, strict=True)
            ]
            self.index.upsert(vectors=vectors, namespace=self.namespace)
            saved += len(vectors)
        return saved

    def search(self, query: str, top_k: int = 10) -> list[VectorSearchResult]:
        embedding = self.embedding_client.embed_text(query)
        response = self.index.query(
            vector=embedding,
            top_k=top_k,
            namespace=self.namespace,
            include_metadata=True,
        )
        matches = _response_matches(response)
        results: list[VectorSearchResult] = []
        for match in matches:
            metadata = dict(_match_metadata(match))
            text = str(metadata.pop("text", ""))
            results.append(
                VectorSearchResult(
                    id=str(_match_value(match, "id")),
                    score=float(_match_value(match, "score") or 0.0),
                    text=text,
                    metadata=metadata,
                )
            )
        return results


def build_claim_vector_documents(
    db: Session,
    *,
    include_patent_abstracts: bool = True,
    include_independent_claims: bool = True,
    include_claim_elements: bool = True,
    limit: int | None = None,
) -> list[ClaimVectorDocument]:
    documents: list[ClaimVectorDocument] = []

    patents_query = db.query(Patent).order_by(Patent.id)
    patents = patents_query.limit(limit).all() if limit else patents_query.all()
    patent_ids = [patent.id for patent in patents]

    if include_patent_abstracts:
        for patent in patents:
            if patent.abstract:
                documents.append(_patent_abstract_document(patent))

    if not patent_ids:
        return documents

    claims_query = (
        db.query(Claim)
        .filter(
            Claim.patent_id.in_(patent_ids),
            Claim.status == "active",
            Claim.is_independent.is_(True),
        )
        .order_by(Claim.patent_id, Claim.claim_number)
    )
    claims = claims_query.all()

    if include_independent_claims:
        documents.extend(_claim_document(claim) for claim in claims)

    if include_claim_elements:
        claim_ids = [claim.id for claim in claims]
        if claim_ids:
            elements = (
                db.query(ClaimElement)
                .filter(ClaimElement.claim_id.in_(claim_ids))
                .order_by(ClaimElement.claim_id, ClaimElement.element_order)
                .all()
            )
            documents.extend(_claim_element_document(element) for element in elements)

    return documents


def _patent_abstract_document(patent: Patent) -> ClaimVectorDocument:
    return ClaimVectorDocument(
        id=f"patent:{patent.id}:abstract",
        text=patent.abstract or "",
        metadata={
            "text_type": TEXT_TYPE_PATENT_ABSTRACT,
            "patent_id": patent.id,
            "application_number": patent.application_number,
            "title": patent.title,
        },
    )


def _claim_document(claim: Claim) -> ClaimVectorDocument:
    patent = claim.patent
    return ClaimVectorDocument(
        id=f"claim:{claim.id}",
        text=claim.normalized_text,
        metadata={
            "text_type": TEXT_TYPE_INDEPENDENT_CLAIM,
            "patent_id": claim.patent_id,
            "claim_id": claim.id,
            "application_number": patent.application_number,
            "title": patent.title,
            "claim_number": claim.claim_number,
            "parser_confidence": claim.parser_confidence or 0.0,
            "parser_status": claim.parser_status or "",
        },
    )


def _claim_element_document(element: ClaimElement) -> ClaimVectorDocument:
    claim = element.claim
    patent = claim.patent
    return ClaimVectorDocument(
        id=f"claim_element:{element.id}",
        text=element.element_text,
        metadata={
            "text_type": TEXT_TYPE_CLAIM_ELEMENT,
            "patent_id": claim.patent_id,
            "claim_id": claim.id,
            "claim_element_id": element.id,
            "application_number": patent.application_number,
            "title": patent.title,
            "claim_number": claim.claim_number,
            "element_order": element.element_order,
            "parser_confidence": element.parser_confidence or 0.0,
            "parser_status": element.parser_status or "",
        },
    )


def _pinecone_index_names(indexes: Any) -> set[str]:
    if hasattr(indexes, "names"):
        return set(indexes.names())
    names: set[str] = set()
    for item in indexes:
        if isinstance(item, str):
            names.add(item)
        elif isinstance(item, dict) and "name" in item:
            names.add(str(item["name"]))
        elif hasattr(item, "name"):
            names.add(str(item.name))
    return names


def _response_matches(response: Any) -> list[Any]:
    if isinstance(response, dict):
        return list(response.get("matches", []))
    return list(getattr(response, "matches", []))


def _match_metadata(match: Any) -> dict[str, Any]:
    if isinstance(match, dict):
        return dict(match.get("metadata", {}))
    return dict(getattr(match, "metadata", {}) or {})


def _match_value(match: Any, key: str) -> Any:
    if isinstance(match, dict):
        return match.get(key)
    return getattr(match, key, None)
