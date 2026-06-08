from typing import TypedDict


class ClaimLensState(TypedDict, total=False):
    product_description: str
    technical_domain: str | None
    product_features: list[str]
    search_queries: list[str]
    patent_candidates: list[dict]
    claim_elements: list[dict]
    comparison_results: list[dict]
    final_report: str


def build_claimlens_graph():
    """ClaimLens LangGraph 워크플로우를 만든다.

    특허 데이터 파이프라인이 준비되면 실제 노드를 이 함수 안에 추가한다.
    API 계층은 이 함수만 호출하게 두면, 내부 워크플로우가 바뀌어도
    라우터와 스트리밍 계층은 안정적으로 유지할 수 있다.
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
            "product_features": [
                "사용자가 입력한 제품/기술 설명을 받았습니다",
                "제품 기능 추출 노드 자리표시자입니다",
            ],
            "search_queries": [description[:80]],
        }

    graph.add_node("analyze_input", analyze_input)
    graph.set_entry_point("analyze_input")
    graph.set_finish_point("analyze_input")
    return graph.compile()
