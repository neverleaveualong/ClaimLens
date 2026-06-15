from app.agents.claimlens_graph import build_claimlens_graph
from app.services.feature_matcher import (
    build_claim_chart_rows,
    extract_product_features,
    match_claim_element,
    validate_claim_chart_rows,
)
from app.services.vector_search import (
    ClaimElementSearchRecord,
    ClaimSearchCandidate,
    ClaimSearchRecord,
    PatentSearchRecord,
)


def make_candidate() -> ClaimSearchCandidate:
    patent = PatentSearchRecord(
        id=1,
        application_number="10-2024-0000001",
        title="문서검색 특허",
        abstract="문서 검색과 키워드 추출에 관한 특허",
        applicant_name=None,
        register_status="등록",
    )
    claim = ClaimSearchRecord(
        id=1,
        claim_number=1,
        raw_text="1. 문서 검색수단; 키워드 추출수단;",
        normalized_text="1. 문서 검색수단; 키워드 추출수단;",
        status="active",
        is_independent=True,
        parser_confidence=0.8,
        parser_status="parsed",
    )
    elements = [
        ClaimElementSearchRecord(
            id=1,
            element_order=1,
            element_text="사용자 질의에 대응하는 문서를 검색하는 검색수단",
            source_span=None,
            parser_confidence=0.8,
            parser_status="parsed",
        ),
        ClaimElementSearchRecord(
            id=2,
            element_order=2,
            element_text="검색된 문서에서 주요 키워드를 추출하는 추출수단",
            source_span=None,
            parser_confidence=0.8,
            parser_status="parsed",
        ),
    ]
    return ClaimSearchCandidate(
        vector_id="claim_element:1",
        score=0.91,
        matched_text=elements[0].element_text,
        matched_text_type="claim_element",
        patent=patent,
        claim=claim,
        matched_claim_element=elements[0],
        claim_elements=elements,
    )


def test_extract_product_features_splits_description_into_clauses() -> None:
    features = extract_product_features(
        "사용자 질의를 입력받고 문서를 검색한다. 검색된 문서에서 키워드를 추출한다."
    )

    assert features == [
        "사용자 질의를 입력받고 문서를 검색한다",
        "검색된 문서에서 키워드를 추출한다",
    ]


def test_match_claim_element_requires_product_evidence_for_match() -> None:
    match = match_claim_element(
        "검색된 문서에서 주요 키워드를 추출하는 추출수단",
        ["검색된 문서에서 키워드를 추출한다"],
    )

    assert match.status == "matched"
    assert match.product_feature == "검색된 문서에서 키워드를 추출한다"
    assert match.evidence is not None


def test_match_claim_element_returns_not_found_without_overlap() -> None:
    match = match_claim_element(
        "검색된 문서에서 주요 키워드를 추출하는 추출수단",
        ["사용자 계정을 관리한다"],
    )

    assert match.status == "not_found"
    assert match.evidence is None
    assert match.uncertainty is not None


def test_build_claim_chart_rows_compares_all_candidate_elements() -> None:
    rows = build_claim_chart_rows(
        [make_candidate()],
        ["사용자 질의로 문서를 검색한다", "검색된 문서에서 키워드를 추출한다"],
    )

    assert [row.claim_element_order for row in rows] == [1, 2]
    assert all(row.evidence for row in rows if row.match_status in {"matched", "partial"})


def test_v1_graph_runs_search_match_and_report_nodes() -> None:
    graph = build_claimlens_graph(candidate_searcher=lambda _: [make_candidate()])

    state = graph.invoke(
        {
            "product_description": "사용자 질의로 문서를 검색하고 검색된 문서에서 키워드를 추출한다.",
            "technical_domain": None,
        }
    )

    assert state["patent_candidates"][0]["patent"]["applicationNumber"] == "10-2024-0000001"
    assert len(state["claim_elements"]) == 2
    assert len(state["comparison_results"]) == 2
    assert state["final_report"].startswith("## 기술 검토 초안")


def test_validate_claim_chart_rows_downgrades_unsupported_match() -> None:
    row = build_claim_chart_rows([make_candidate()], ["사용자 질의로 문서를 검색한다"])[0]
    unsupported = row.__class__(
        **{
            **row.__dict__,
            "match_status": "matched",
            "evidence": None,
        }
    )

    validated = validate_claim_chart_rows([unsupported])

    assert validated[0].match_status == "uncertain"
    assert validated[0].uncertainty is not None
