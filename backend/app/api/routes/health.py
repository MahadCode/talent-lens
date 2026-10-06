from fastapi import APIRouter
from pydantic import BaseModel
class MessageResponse(BaseModel):
    message: str
router = APIRouter(prefix="/health", tags=["Health"])
@router.get("", response_model=MessageResponse)
async def health() -> MessageResponse:
    return MessageResponse(message="ok")
