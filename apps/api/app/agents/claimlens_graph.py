from collections.abc import Callable
from typing import Any, TypedDict

from app.services.feature_matcher import (
    build_claim_chart_rows,
    claim_candidate_to_dict,
    claim_chart_row_to_event_data,
    extract_product_features,
    generate_claim_chart_report,
)
from app.services.vector_search import ClaimSearchCandidate


class ClaimLensState(TypedDict, total=False):
    product_description: str
    technical_domain: str | None
    product_features: list[str]
    search_queries: list[str]
    patent_candidates: list[dict[str, Any]]
    claim_elements: list[dict[str, Any]]
    comparison_results: list[dict[str, Any]]
    final_report: str
    _search_candidates: list[ClaimSearchCandidate]
    _claim_chart_rows: list[Any]


CandidateSearcher = Callable[[str], list[ClaimSearchCandidate]]


def build_claimlens_graph(candidate_searcher: CandidateSearcher | None = None):
    """ClaimLens V1 순차 워크플로우를 만든다.

    Phase 5에서는 Supervisor 없이 입력 분석, 검색, claim element 로드,
    매칭, 리포트 생성을 고정 순서로 실행한다.
    """
    try:
        from langgraph.graph import StateGraph
    except ImportError as exc:
        raise RuntimeError("LangGraph가 설치되어 있지 않습니다. pip install -e '.[dev]'를 실행하세요.") from exc

    graph = StateGraph(ClaimLensState)

    def analyze_input(state: ClaimLensState) -> ClaimLensState:
        description = state["product_description"]
        return {
            **state,
            "product_features": extract_product_features(description),
            "search_queries": [description[:80]],
        }

    def search_patents(state: ClaimLensState) -> ClaimLensState:
        description = state["product_description"]
        candidates = candidate_searcher(description) if candidate_searcher else []
        return {
            **state,
            "_search_candidates": candidates,
            "patent_candidates": [claim_candidate_to_dict(candidate) for candidate in candidates],
        }

    def load_claim_elements(state: ClaimLensState) -> ClaimLensState:
        candidates = state.get("_search_candidates", [])
        elements: list[dict[str, Any]] = []
        for candidate in candidates:
            for element in candidate.claim_elements:
                elements.append(
                    {
                        "applicationNumber": candidate.patent.application_number,
                        "claimNumber": candidate.claim.claim_number if candidate.claim else None,
                        "elementOrder": element.element_order,
                        "elementText": element.element_text,
                    }
                )
        return {**state, "claim_elements": elements}

    def match_features(state: ClaimLensState) -> ClaimLensState:
        rows = build_claim_chart_rows(
            state.get("_search_candidates", []),
            state.get("product_features", []),
        )
        return {
            **state,
            "_claim_chart_rows": rows,
            "comparison_results": [claim_chart_row_to_event_data(row) for row in rows],
        }

    def generate_report(state: ClaimLensState) -> ClaimLensState:
        return {
            **state,
            "final_report": generate_claim_chart_report(state.get("_claim_chart_rows", [])),
        }

    graph.add_node("analyze_input", analyze_input)
    graph.add_node("search_patents", search_patents)
    graph.add_node("load_claim_elements", load_claim_elements)
    graph.add_node("match_features", match_features)
    graph.add_node("generate_report", generate_report)
    graph.set_entry_point("analyze_input")
    graph.add_edge("analyze_input", "search_patents")
    graph.add_edge("search_patents", "load_claim_elements")
    graph.add_edge("load_claim_elements", "match_features")
    graph.add_edge("match_features", "generate_report")
    graph.set_finish_point("generate_report")
    return graph.compile()
