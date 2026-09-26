from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.schemas.analysis import AnalysisRequest, AnalysisResponse
from backend.app.schemas.weather import WeatherErrorResponse
from backend.app.orchestration.workflow import pipeline
from backend.app.core.exceptions import WeatherServiceException
from backend.app.monitoring.logger import logger

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalysisResponse,
    responses={
        404: {"model": WeatherErrorResponse, "description": "Location could not be resolved"},
        504: {"model": WeatherErrorResponse, "description": "Weather API timed out"},
        502: {"model": WeatherErrorResponse, "description": "Upstream Weather API error"},
        422: {"model": WeatherErrorResponse, "description": "Malformed response schema"},
    }
)
async def analyze_weather_intent(request: AnalysisRequest):
    """Executes the multi-agent pipeline synchronously."""
    clean_location = request.location.strip()
    clean_query = request.query.strip()

    if not clean_location:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "error_code": "INVALID_INPUT",
                "message": "Location field cannot be empty.",
                "location_searched": request.location,
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    if not clean_query:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "error_code": "INVALID_INPUT",
                "message": "Query field cannot be empty.",
                "location_searched": request.location,
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    try:
        response = await pipeline.run(request)
        return response
    except WeatherServiceException as wse:
        logger.warning(f"Pipeline weather fetch failed: [{wse.error_code}] {wse.message}")
        raise HTTPException(
            status_code=wse.status_code,
            detail={
                "error": True,
                "error_code": wse.error_code,
                "message": wse.message,
                "detail": wse.detail,
                "location_searched": clean_location,
                "retries_attempted": wse.retries_attempted,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-agent analysis pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": f"Analysis pipeline error: {str(e)}",
                "location_searched": clean_location,
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


@router.post("/stream")
async def analyze_weather_intent_stream(request: AnalysisRequest):
    """Executes the multi-agent pipeline and streams live Server-Sent Events (SSE) of actual tasks running."""
    clean_location = request.location.strip()
    clean_query = request.query.strip()

    if not clean_location:
        raise HTTPException(status_code=400, detail="Location field cannot be empty.")
    if not clean_query:
        raise HTTPException(status_code=400, detail="Query field cannot be empty.")

    return StreamingResponse(
        pipeline.run_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
