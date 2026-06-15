from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.patent import Claim, ClaimElement, Patent
from app.services.vector_search import (
    TEXT_TYPE_CLAIM_ELEMENT,
    TEXT_TYPE_INDEPENDENT_CLAIM,
    TEXT_TYPE_PATENT_ABSTRACT,
    ClaimVectorDocument,
    PineconeClaimVectorIndex,
    VectorSearchResult,
    build_claim_vector_documents,
    resolve_vector_search_results,
    search_claim_candidates,
)


class FakeEmbeddingClient:
    def embed_text(self, text: str) -> list[float]:
        return [float(len(text)), 1.0, 0.0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0, 0.0] for text in texts]


class FakePineconeIndex:
    def __init__(self) -> None:
        self.upserts: list[dict] = []
        self.queries: list[dict] = []

    def upsert(self, vectors: list[dict], namespace: str) -> None:
        self.upserts.append({"vectors": vectors, "namespace": namespace})

    def query(
        self,
        *,
        vector: list[float],
        top_k: int,
        namespace: str,
        include_metadata: bool,
    ) -> dict:
        self.queries.append(
            {
                "vector": vector,
                "top_k": top_k,
                "namespace": namespace,
                "include_metadata": include_metadata,
            }
        )
        return {
            "matches": [
                {
                    "id": "claim_element:1",
                    "score": 0.91,
                    "metadata": {
                        "text": "키워드를 추출하기 위한 추출수단",
                        "text_type": TEXT_TYPE_CLAIM_ELEMENT,
                        "patent_id": 1,
                        "claim_id": 1,
                        "claim_element_id": 2,
                        "application_number": "10-2024-0000001",
                        "title": "문서검색 특허",
                        "claim_number": 1,
                        "element_order": 2,
                    },
                }
            ]
        }


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def seed_patent(db):
    patent = Patent(
        application_number="10-2024-0000001",
        application_number_normalized="1020240000001",
        title="문서검색 특허",
        abstract="문서 검색과 키워드 추출에 관한 특허",
        source="kipris",
        fetch_status="fetched",
    )
    db.add(patent)
    db.flush()

    independent_claim = Claim(
        patent_id=patent.id,
        claim_number=1,
        raw_text="1. 데이터베이스; 키워드를 추출하기 위한 추출수단;",
        normalized_text="1. 데이터베이스; 키워드를 추출하기 위한 추출수단;",
        status="active",
        is_independent=True,
        source_endpoint="patentClaimInfo",
        source_document_type="claim_endpoint",
        parser_confidence=0.75,
        parser_method="rule_based",
        parser_status="parsed",
    )
    dependent_claim = Claim(
        patent_id=patent.id,
        claim_number=2,
        raw_text="2. 제 1 항에 있어서, 검색수단",
        normalized_text="2. 제 1 항에 있어서, 검색수단",
        status="active",
        is_independent=False,
        source_endpoint="patentClaimInfo",
        source_document_type="claim_endpoint",
        parser_confidence=0.55,
        parser_method="fallback",
        parser_status="uncertain",
    )
    db.add_all([independent_claim, dependent_claim])
    db.flush()

    db.add_all(
        [
            ClaimElement(
                claim_id=independent_claim.id,
                element_order=1,
                element_text="문서가 저장되는 데이터베이스",
                parser_confidence=0.75,
                parser_method="rule_based",
                parser_status="parsed",
            ),
            ClaimElement(
                claim_id=independent_claim.id,
                element_order=2,
                element_text="키워드를 추출하기 위한 추출수단",
                parser_confidence=0.75,
                parser_method="rule_based",
                parser_status="parsed",
            ),
        ]
    )
    db.commit()


def test_build_claim_vector_documents_indexes_independent_claims_and_elements() -> None:
    db = make_session()
    seed_patent(db)

    documents = build_claim_vector_documents(db)

    assert [document.id for document in documents] == [
        "patent:1:abstract",
        "claim:1",
        "claim_element:1",
        "claim_element:2",
    ]
    assert documents[1].metadata["text_type"] == TEXT_TYPE_INDEPENDENT_CLAIM
    assert documents[2].metadata["text_type"] == TEXT_TYPE_CLAIM_ELEMENT
    assert all(document.metadata["application_number"] == "10-2024-0000001" for document in documents)


def test_pinecone_claim_vector_index_upserts_with_text_metadata() -> None:
    fake_index = FakePineconeIndex()
    vector_index = PineconeClaimVectorIndex(
        namespace="test",
        embedding_client=FakeEmbeddingClient(),
        pinecone_client=None,
        index=fake_index,
    )

    saved = vector_index.upsert_documents(
        [
            ClaimVectorDocument(
                id="claim_element:1",
                text="키워드를 추출하기 위한 추출수단",
                metadata={"text_type": TEXT_TYPE_CLAIM_ELEMENT},
            )
        ]
    )

    assert saved == 1
    assert fake_index.upserts[0]["namespace"] == "test"
    vector = fake_index.upserts[0]["vectors"][0]
    assert vector["id"] == "claim_element:1"
    assert vector["metadata"]["text"] == "키워드를 추출하기 위한 추출수단"


def test_pinecone_claim_vector_index_search_returns_normalized_results() -> None:
    fake_index = FakePineconeIndex()
    vector_index = PineconeClaimVectorIndex(
        namespace="test",
        embedding_client=FakeEmbeddingClient(),
        pinecone_client=None,
        index=fake_index,
    )

    results = vector_index.search("문서에서 키워드를 추출한다", top_k=3)

    assert fake_index.queries[0]["namespace"] == "test"
    assert fake_index.queries[0]["top_k"] == 3
    assert results[0].id == "claim_element:1"
    assert results[0].score == 0.91
    assert results[0].text == "키워드를 추출하기 위한 추출수단"
    assert results[0].metadata["text_type"] == TEXT_TYPE_CLAIM_ELEMENT


def test_resolve_vector_search_results_loads_postgres_source_records() -> None:
    db = make_session()
    seed_patent(db)

    candidates = resolve_vector_search_results(
        db,
        [
            VectorSearchResult(
                id="claim_element:2",
                score=0.91,
                text="키워드를 추출하기 위한 추출수단",
                metadata={
                    "text_type": TEXT_TYPE_CLAIM_ELEMENT,
                    "patent_id": 1,
                    "claim_id": 1,
                    "claim_element_id": 2,
                },
            )
        ],
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.patent.application_number == "10-2024-0000001"
    assert candidate.claim is not None
    assert candidate.claim.claim_number == 1
    assert candidate.matched_claim_element is not None
    assert candidate.matched_claim_element.element_order == 2
    assert [element.element_order for element in candidate.claim_elements] == [1, 2]


def test_resolve_vector_search_results_supports_patent_level_matches() -> None:
    db = make_session()
    seed_patent(db)

    candidates = resolve_vector_search_results(
        db,
        [
            VectorSearchResult(
                id="patent:1:abstract",
                score=0.82,
                text="문서 검색과 키워드 추출에 관한 특허",
                metadata={
                    "text_type": TEXT_TYPE_PATENT_ABSTRACT,
                    "patent_id": 1,
                },
            )
        ],
    )

    assert len(candidates) == 1
    assert candidates[0].patent.title == "문서검색 특허"
    assert candidates[0].claim is None
    assert candidates[0].matched_claim_element is None
    assert candidates[0].claim_elements == []


def test_search_claim_candidates_searches_vectors_and_resolves_candidates() -> None:
    db = make_session()
    seed_patent(db)
    fake_index = FakePineconeIndex()
    vector_index = PineconeClaimVectorIndex(
        namespace="test",
        embedding_client=FakeEmbeddingClient(),
        pinecone_client=None,
        index=fake_index,
    )

    candidates = search_claim_candidates(
        db,
        "문서에서 키워드를 추출한다",
        top_k=3,
        vector_index=vector_index,
    )

    assert fake_index.queries[0]["top_k"] == 3
    assert candidates[0].matched_text_type == TEXT_TYPE_CLAIM_ELEMENT
    assert candidates[0].patent.title == "문서검색 특허"
