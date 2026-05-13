from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database import get_db
from models import User, Analysis, Subscription, Conversation
from services.openai_service import generate_response, chat_with_bot
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/generate", tags=["generate"])

VALID_CHAT_MODES = ["friend", "psychologist", "coach", "honest", "stylist"]
VALID_GENERATE_MODES = ["flirt", "put_in_place", "joke", "soft_reject", "support"]
PREMIUM_CHAT_MODES = ["psychologist", "coach", "honest", "stylist"]
FREE_RESPONSES_LIMIT = 1

async def get_plan(user: User, db: AsyncSession) -> str:
    if not user.is_premium:
        return "free"
    sub_result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                Subscription.ends_at > datetime.now()
            )
        ).order_by(Subscription.started_at.desc()).limit(1)
    )
    sub = sub_result.scalars().first()
    if not sub:
        return "love_pro"
    payment = sub.payment_type or ""
    if "vip" in payment or payment == "referral_vip":
        return "vip"
    return "love_pro"


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

    plan = await get_plan(user, db)

    if plan == "free":
        responses_used = user.free_responses_used or 0
        if responses_used >= FREE_RESPONSES_LIMIT:
            raise HTTPException(
                status_code=403,
                detail="UPGRADE_REQUIRED:Безкоштовна генерація відповіді використана (1/1). Отримай Love Pro 💜 для безліміту"
            )

    analysis_result = await db.execute(select(Analysis).where(Analysis.id == request.analysis_id))
    analysis = analysis_result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Аналіз не знайдено")

    variants = await generate_response({
        "summary": analysis.summary,
        "user_style": analysis.user_style,
        "tone": analysis.tone,
        "interest_level": analysis.interest_level
    }, request.mode)

    # Рахуємо використану генерацію для фрі
    if plan == "free":
        user.free_responses_used = (user.free_responses_used or 0) + 1
        await db.commit()

    return {"variants": variants}


@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    if request.mode not in VALID_CHAT_MODES:
        raise HTTPException(status_code=400, detail="Невірний режим чату")

    result = await db.execute(select(User).where(User.telegram_id == request.telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    plan = await get_plan(user, db)
    if plan == "free" and request.mode in PREMIUM_CHAT_MODES:
        raise HTTPException(
            status_code=403,
            detail="UPGRADE_REQUIRED:Цей режим чату доступний в Love Pro 💜 або VIP 👑"
        )

    response = await chat_with_bot(request.messages, request.mode)

    conv = Conversation(
        user_id=user.id,
        mode=request.mode,
        messages=request.messages
    )
    db.add(conv)
    await db.commit()

    return {"response": response}
