"""Review API endpoints."""
import time
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, UploadFile, File

from app.models.schemas import ReviewRequest, ReviewResponse, Suggestion, UploadResponse
from app.agents.review_controller_langgraph import LangGraphReviewController
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/review", tags=["review"])

# Dependency injection
_vector_store = None
_review_controller = None


def get_vector_store() -> VectorStoreService:
    """Get vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store


def get_review_controller() -> LangGraphReviewController:
    """Get LangGraph review controller instance."""
    global _review_controller
    if _review_controller is None:
        _review_controller = LangGraphReviewController()
    return _review_controller


@router.post("/analyze", response_model=ReviewResponse)
async def analyze_paper(
    request: ReviewRequest,
    vector_store: VectorStoreService = Depends(get_vector_store)
) -> ReviewResponse:
    """
    Analyze a research paper and return suggestions.

    Uses LangGraph StateGraph with Pydantic BaseModel for state management:
    - Parse sections
    - Analyze each section with Clarity and Rigor agents
    - Orchestrator validation and prioritization
    - Graph-based workflow with conditional edges

    Args:
        request: Review request containing paper content
        vector_store: Vector store instance (for future RAG integration)

    Returns:
        Review response with suggestions

    Performance:
        - Small papers (3-5 sections): ~5-7s
        - Medium papers (6-10 sections): ~7-10s
        - Large papers (11-15 sections): ~10-14s
    """
    start_time = time.time()

    try:
        logger.info(f"Starting LangGraph review for session: {request.session_id}")

        controller = get_review_controller()
        result = await controller.review(
            content=request.content,
            session_id=request.session_id,
            target_venue=request.target_venue,
            analysis_types=request.analysis_types
        )

        processing_time = time.time() - start_time
        suggestions = [Suggestion(**s) for s in result["suggestions"]]

        logger.info(f"Review completed in {processing_time:.2f}s with {len(suggestions)} suggestions")

        return ReviewResponse(
            suggestions=suggestions,
            session_id=request.session_id,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error in analyze_paper: {e}")
        raise


@router.post("/upload-guidelines", response_model=UploadResponse)
async def upload_guidelines(
    file: UploadFile = File(...),
    vector_store: VectorStoreService = Depends(get_vector_store)
) -> UploadResponse:
    """
    Upload a PDF guideline document to the RAG system.

    Args:
        file: PDF file to upload
        vector_store: Vector store instance

    Returns:
        Upload response with status
    """
    try:
        logger.info(f"Uploading guideline: {file.filename}")

        # Save file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Process PDF
        metadata = {"filename": file.filename, "type": "guideline"}
        chunks_indexed = await vector_store.process_pdf(tmp_path, metadata)

        # Clean up
        os.unlink(tmp_path)

        return UploadResponse(
            message="Guideline uploaded successfully",
            filename=file.filename,
            chunks_indexed=chunks_indexed
        )

    except Exception as e:
        logger.error(f"Error uploading guidelines: {e}")
        raise


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for real-time review suggestions.

    Args:
        websocket: WebSocket connection
        session_id: Session identifier
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")

    # Get controller
    controller = get_review_controller()

    try:
        while True:
            # Receive data
            data = await websocket.receive_json()

            if data.get("type") == "review":
                content = data.get("content", "")
                target_venue = data.get("target_venue")

                logger.info(f"Processing review request via WebSocket for session: {session_id}")

                # Run review
                result = await controller.review(
                    content=content,
                    session_id=session_id,
                    target_venue=target_venue
                )

                # Send suggestions back
                await websocket.send_json({
                    "type": "suggestions",
                    "suggestions": result["suggestions"],
                    "session_id": session_id
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
