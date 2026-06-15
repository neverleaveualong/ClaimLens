import asyncio
import json
from collections.abc import AsyncIterator

from app.agents.claimlens_graph import build_claimlens_graph
from app.db.session import SessionLocal
from app.schemas.analysis import AgentEvent, AnalysisRequest
from app.services.vector_search import search_claim_candidates


def encode_sse(event: AgentEvent) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"


async def stream_analysis(request: AnalysisRequest) -> AsyncIterator[str]:
    steps = [
        ("input_analysis", "제품/기술 설명을 분석하는 중입니다."),
        ("patent_search", "벡터 DB에서 관련 특허 후보를 검색하는 중입니다."),
        ("claim_loading", "검색 후보의 청구항 구성요소를 불러오는 중입니다."),
        ("feature_matching", "청구항 구성요소를 제품 기능과 비교하는 중입니다."),
        ("report_generation", "기술 검토 리포트를 작성하는 중입니다."),
    ]

    for step, message in steps:
        yield encode_sse(AgentEvent(type="step_started", step=step, message=message))
        await asyncio.sleep(0.1)

    try:
        state = _run_v1_workflow(request)
    except Exception as exc:
        yield encode_sse(
            AgentEvent(
                type="error",
                step="analysis",
                message="분석 워크플로우 실행 중 오류가 발생했습니다.",
                data={"error": str(exc)},
            )
        )
        return

    yield encode_sse(
        AgentEvent(
            type="tool_result",
            step="input_analysis",
            tool="extract_product_features",
            data={"features": state.get("product_features", [])},
        )
    )
    yield encode_sse(
        AgentEvent(
            type="tool_result",
            step="patent_search",
            tool="search_claim_candidates",
            data={"candidates": state.get("patent_candidates", [])[:5]},
        )
    )
    yield encode_sse(
        AgentEvent(
            type="tool_result",
            step="claim_loading",
            tool="load_claim_elements",
            data={"claimElementCount": len(state.get("claim_elements", []))},
        )
    )

    for step, _ in steps:
        yield encode_sse(AgentEvent(type="step_completed", step=step))

    for row in state.get("comparison_results", []):
        yield encode_sse(AgentEvent(type="claim_chart_row", data=row))

    yield encode_sse(
        AgentEvent(
            type="final_report",
            data={"markdown": state.get("final_report", "")},
        )
    )


def _run_v1_workflow(request: AnalysisRequest) -> dict:
    with SessionLocal() as db:
        graph = build_claimlens_graph(
            candidate_searcher=lambda query: search_claim_candidates(db, query, top_k=5)
        )
        return graph.invoke(
            {
                "product_description": request.product_description,
                "technical_domain": request.technical_domain,
            }
        )
