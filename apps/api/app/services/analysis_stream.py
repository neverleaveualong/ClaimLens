import asyncio
import json
from collections.abc import AsyncIterator

from app.schemas.analysis import AgentEvent, AnalysisRequest


def encode_sse(event: AgentEvent) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"


async def stream_analysis(request: AnalysisRequest) -> AsyncIterator[str]:
    steps = [
        ("input_analysis", "제품/기술 설명을 분석하는 중입니다."),
        ("patent_search", "특허 검색 질의를 준비하는 중입니다."),
        ("claim_parsing", "청구항 구성요소 추출을 준비하는 중입니다."),
        ("feature_matching", "청구항과 제품 기능 비교를 준비하는 중입니다."),
        ("report_generation", "기술 검토 리포트를 준비하는 중입니다."),
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
                "claimElement": "청구항 구성요소 자리표시자",
                "productFeature": "제품 기능 자리표시자",
                "match": "needs_review",
                "evidence": "아직 특허 데이터셋 파이프라인이 연결되지 않았습니다.",
            },
        )
    )
    yield encode_sse(
        AgentEvent(
            type="final_report",
            data={
                "markdown": "## 초안 리포트\n\nClaimLens 백엔드와 SSE 워크플로우는 다음 구현 단계로 넘어갈 준비가 되어 있습니다."
            },
        )
    )
