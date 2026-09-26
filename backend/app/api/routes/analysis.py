from fastapi import APIRouter, HTTPException
from backend.app.schemas.analysis import AnalysisRequest, AnalysisResponse
from backend.app.orchestration.workflow import pipeline
from backend.app.monitoring.logger import logger

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("", response_model=AnalysisResponse)
async def analyze_weather_intent(request: AnalysisRequest):
    """Executes the multi-agent pipeline to generate comprehensive weather intelligence."""
    try:
        if not request.location.strip():
            raise HTTPException(status_code=400, detail="Location field cannot be empty.")
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query field cannot be empty.")

        response = await pipeline.run(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-agent analysis pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")
