import asyncio
import json
from collections.abc import AsyncIterator

from app.schemas.analysis import AgentEvent, AnalysisRequest


def encode_sse(event: AgentEvent) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"


async def stream_analysis(request: AnalysisRequest) -> AsyncIterator[str]:
    steps = [
        ("input_analysis", "Analyzing product description."),
        ("patent_search", "Preparing patent search queries."),
        ("claim_parsing", "Preparing claim element extraction."),
        ("feature_matching", "Preparing claim-feature comparison."),
        ("report_generation", "Preparing risk report."),
    ]

    for step, message in steps:
        yield encode_sse(AgentEvent(type="step_started", step=step, message=message))
        await asyncio.sleep(0.1)
        yield encode_sse(
            AgentEvent(
                type="tool_called",
                step=step,
                tool=f"{step}_tool",
                data={"preview": request.product_description[:120]},
            )
        )
        await asyncio.sleep(0.1)
        yield encode_sse(AgentEvent(type="step_completed", step=step))

    yield encode_sse(
        AgentEvent(
            type="claim_chart_row",
            data={
                "claimElement": "Placeholder claim element",
                "productFeature": "Placeholder product feature",
                "match": "needs_review",
                "evidence": "Patent dataset pipeline is not connected yet.",
            },
        )
    )
    yield encode_sse(
        AgentEvent(
            type="final_report",
            data={
                "markdown": "## Draft Report\n\nClaimLens backend and SSE workflow are ready for the next implementation milestone."
            },
        )
    )
