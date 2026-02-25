from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, Analysis
from services.openai_service import generate_response, chat_with_bot
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/generate", tags=["generate"])

VALID_CHAT_MODES = ["friend", "psychologist", "coach", "honest", "stylist"]
VALID_GENERATE_MODES = ["flirt", "put_in_place", "joke", "soft_reject", "support"]

class GenerateRequest(BaseModel):
    telegram_id: str
    analysis_id: int
    mode: str

class ChatRequest(BaseModel):
    telegram_id: str
    mode: str
    messages: List[dict]

@router.post("/response")
async def generate(request: GenerateRequest, db: AsyncSession = Depends(get_db)):
    if request.mode not in VALID_GENERATE_MODES:
        raise HTTPException(status_code=400, detail="Невірний режим генерації")

    result = await db.execute(select(User).where(User.telegram_id == request.telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

#    if not user.is_premium:
#        raise HTTPException(status_code=403, detail="Генератор відповідей доступний тільки в Premium")

    analysis_result = await db.execute(select(Analysis).where(Analysis.id == request.analysis_id))
    analysis = analysis_result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Аналіз не знайдено")

    analysis_dict = {
        "summary": analysis.summary,
        "user_style": analysis.user_style,
        "tone": analysis.tone,
        "interest_level": analysis.interest_level
    }

    variants = await generate_response(analysis_dict, request.mode)
    return {"variants": variants}


@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    if request.mode not in VALID_CHAT_MODES:
        raise HTTPException(status_code=400, detail="Невірний режим чату")

    result = await db.execute(select(User).where(User.telegram_id == request.telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    response = await chat_with_bot(request.messages, request.mode)
    return {"response": response}