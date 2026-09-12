from fastapi import APIRouter, Depends

from api.schemas import SourceExtraction, SourceExtractRequest
from api.services import AIService, get_ai_service

router = APIRouter(prefix="/leads", tags=["source-extraction"])


# POST /leads/source-extract
@router.post("/source-extract", response_model=SourceExtraction)
def extract_lead_source(
    payload: SourceExtractRequest,
    ai_service: AIService = Depends(get_ai_service),
) -> SourceExtraction:
    """
    POST /leads/source-extract

    Extracts structured source channel and specific evidence details from lead notes.

    Params:
        payload (SourceExtractRequest): Request payload containing raw notes text.
        ai_service (AIService): Injected AI service dependency.

    Returns:
        SourceExtraction: Extracted source channel and detail.
    """
    return ai_service.extract_source(payload.text)
