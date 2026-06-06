from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.analysis import AnalysisRequest
from app.services.analysis_stream import stream_analysis

router = APIRouter()


@router.post("/analyses/stream")
async def create_analysis_stream(request: AnalysisRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_analysis(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
