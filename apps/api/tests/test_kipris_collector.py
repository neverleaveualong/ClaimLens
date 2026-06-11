from collections.abc import Iterable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients.kipris import ClaimInfoResult, PatentSearchResult
from app.db.base import Base
from app.models.patent import Claim, ClaimElement, Patent
from app.services.kipris_collector import KiprisCollector


class FakeKiprisClient:
    def __init__(
        self,
        candidates: Iterable[PatentSearchResult] = (),
        claim_results: dict[str, ClaimInfoResult | Exception] | None = None,
    ) -> None:
        self.candidates = list(candidates)
        self.claim_results = claim_results or {}

    def search_patents(self, keyword: str, limit: int = 10) -> list[PatentSearchResult]:
        return self.candidates[:limit]

    def get_claims(self, application_number: str) -> ClaimInfoResult:
        result = self.claim_results[application_number]
        if isinstance(result, Exception):
            raise result
        return result


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def make_claim_result(
    application_number: str,
    claims: list[str] | None = None,
    source_endpoint: str = "patentClaimInfo",
    source_document_type: str = "claim_endpoint",
) -> ClaimInfoResult:
    return ClaimInfoResult(
        application_number=application_number,
        claims=claims or ["1. 입력수단; 처리수단"],
        result_code="00",
        result_message="NORMAL SERVICE.",
        source_endpoint=source_endpoint,
        source_document_type=source_document_type,
    )


def test_application_number_collection_preserves_existing_metadata() -> None:
    db = make_session()
    db.add(
        Patent(
            application_number="10-2024-0000001",
            application_number_normalized="1020240000001",
            title="기존 제목",
            abstract="기존 초록",
            applicant_name="기존 출원인",
            ipc_number="G06F",
            source="kipris",
            fetch_status="fetched",
        )
    )
    db.commit()

    client = FakeKiprisClient(
        claim_results={
            "10-2024-0000001": make_claim_result("10-2024-0000001"),
        }
    )
    collector = KiprisCollector(db=db, client=client)

    result = collector.collect_by_application_number("10-2024-0000001")

    patent = db.query(Patent).one()
    assert result.fetch_status == "fetched"
    assert patent.title == "기존 제목"
    assert patent.abstract == "기존 초록"
    assert patent.applicant_name == "기존 출원인"
    assert patent.ipc_number == "G06F"


def test_keyword_collection_keeps_successes_when_one_candidate_fails() -> None:
    db = make_session()
    candidates = [
        PatentSearchResult(application_number="10-2024-0000001", title="성공 특허"),
        PatentSearchResult(application_number="10-2024-0000002", title="실패 특허"),
    ]
    client = FakeKiprisClient(
        candidates=candidates,
        claim_results={
            "10-2024-0000001": make_claim_result("10-2024-0000001"),
            "10-2024-0000002": RuntimeError("KIPRIS timeout"),
        },
    )
    collector = KiprisCollector(db=db, client=client)

    summary = collector.collect_by_keyword("문서검색", limit=2)

    assert summary.requested_count == 2
    assert summary.saved_patent_count == 1
    assert summary.failed_patent_count == 1

    patents = {patent.application_number: patent for patent in db.query(Patent).all()}
    assert patents["10-2024-0000001"].fetch_status == "fetched"
    assert patents["10-2024-0000002"].fetch_status == "fetch_failed"


def test_collector_stores_claim_source_from_fallback_result() -> None:
    db = make_session()
    client = FakeKiprisClient(
        claim_results={
            "10-2024-0000001": make_claim_result(
                "10-2024-0000001",
                source_endpoint="getBibliographyDetailInfoSearch",
                source_document_type="bibliography_detail",
            ),
        }
    )
    collector = KiprisCollector(db=db, client=client)

    collector.collect_by_application_number("10-2024-0000001")

    claim = db.query(Claim).one()
    assert claim.source_endpoint == "getBibliographyDetailInfoSearch"
    assert claim.source_document_type == "bibliography_detail"


def test_collector_stores_claim_element_source_spans() -> None:
    db = make_session()
    client = FakeKiprisClient(
        claim_results={
            "10-2024-0000001": make_claim_result(
                "10-2024-0000001",
                claims=["1. 문서를 저장하는 저장수단; 사용자 질의를 입력받는 입력수단;"],
            ),
        }
    )
    collector = KiprisCollector(db=db, client=client)

    collector.collect_by_application_number("10-2024-0000001")

    elements = db.query(ClaimElement).order_by(ClaimElement.element_order).all()
    assert [element.element_text for element in elements] == [
        "문서를 저장하는 저장수단",
        "사용자 질의를 입력받는 입력수단",
    ]
    assert [element.source_span for element in elements] == [
        "문서를 저장하는 저장수단",
        "사용자 질의를 입력받는 입력수단",
    ]
    assert all(element.parser_confidence == 0.75 for element in elements)
