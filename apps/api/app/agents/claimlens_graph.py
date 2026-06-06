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
    """Create the LangGraph workflow.

    The concrete nodes will be added after the patent data pipeline is ready.
    Keeping this function as the graph boundary makes the API layer stable while
    the workflow evolves.
    """
    try:
        from langgraph.graph import StateGraph
    except ImportError as exc:
        raise RuntimeError("LangGraph is not installed. Run pip install -e '.[dev]'.") from exc

    graph = StateGraph(ClaimLensState)

    def analyze_input(state: ClaimLensState) -> ClaimLensState:
        description = state["product_description"]
        return {
            **state,
            "product_features": [
                "User-provided product description accepted",
                "Feature extraction node placeholder",
            ],
            "search_queries": [description[:80]],
        }

    graph.add_node("analyze_input", analyze_input)
    graph.set_entry_point("analyze_input")
    graph.set_finish_point("analyze_input")
    return graph.compile()
