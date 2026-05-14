from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, Subscription, OutfitAnalysis
from services.achievements import update_streak, check_and_award
from pydantic import BaseModel
from typing import Optional
import hashlib
from datetime import datetime, timedelta

router = APIRouter(prefix="/users", tags=["users"])

def generate_referral_code(telegram_id: str) -> str:
    return hashlib.md5(telegram_id.encode()).hexdigest()[:8].upper()

async def apply_referral_reward(referrer: User, db: AsyncSession):
    count = referrer.referral_count or 0
    print(f"REFERRAL REWARD CHECK: count={count} for {referrer.telegram_id}")

    if count == 2:
        referrer.bonus_analyses = (referrer.bonus_analyses or 0) + 10
        print(f"REFERRAL REWARD: +10 analyses for {referrer.telegram_id}")

    elif count == 5:
        referrer.is_premium = True
        sub = Subscription(
            user_id=referrer.id,
            status="active",
            started_at=datetime.now(),
            ends_at=datetime.now() + timedelta(weeks=1),
            payment_type="referral_love_pro"
        )
        db.add(sub)
        print(f"REFERRAL REWARD: Love Pro 1 week for {referrer.telegram_id}")

    elif count == 10:
        referrer.is_premium = True
        sub = Subscription(
            user_id=referrer.id,
            status="active",
            started_at=datetime.now(),
            ends_at=datetime.now() + timedelta(weeks=2),
            payment_type="referral_vip"
        )
        db.add(sub)
        print(f"REFERRAL REWARD: VIP 2 weeks for {referrer.telegram_id}")


class UserCreate(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    referral_code: Optional[str] = None


@router.post("/")
async def create_or_get_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == user_data.telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            referral_code=generate_referral_code(user_data.telegram_id),
            last_active_at=datetime.now()
        )
        db.add(user)
        await db.flush()

        if user_data.referral_code:
            referrer_result = await db.execute(
                select(User).where(User.referral_code == user_data.referral_code)
            )
            referrer = referrer_result.scalar_one_or_none()
            if referrer and referrer.telegram_id != user_data.telegram_id:
                user.referred_by = referrer.id
                referrer.referral_count = (referrer.referral_count or 0) + 1
                await apply_referral_reward(referrer, db)
                print(f"REFERRAL NEW: {user_data.telegram_id} -> {referrer.telegram_id}, count={referrer.referral_count}")

        await db.commit()
        await db.refresh(user)

    else:
        user.last_active_at = datetime.now()

        if user_data.referral_code and not user.referred_by:
            referrer_result = await db.execute(
                select(User).where(User.referral_code == user_data.referral_code)
            )
            referrer = referrer_result.scalar_one_or_none()
            if referrer and referrer.telegram_id != user_data.telegram_id:
                user.referred_by = referrer.id
                referrer.referral_count = (referrer.referral_count or 0) + 1
                await apply_referral_reward(referrer, db)
                print(f"REFERRAL EXISTING: {user_data.telegram_id} -> {referrer.telegram_id}, count={referrer.referral_count}")

        # Оновлюємо streak при кожному відкритті
        await update_streak(user, db)
        await db.flush()

        # Перевіряємо досягнення
        try:
            from bot import bot
            await check_and_award(user, db, bot)
        except Exception as e:
            print(f"achievements error: {e}")

        await db.commit()
        await db.refresh(user)

    return await _user_response(user, db)


@router.post("/create-invoice")
async def create_invoice(
    telegram_id: str,
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    from bot import bot, PLANS
    from aiogram.types import LabeledPrice

    plan = PLANS.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="План не знайдено")

    await bot.send_invoice(
        chat_id=int(telegram_id),
        title=plan["title"],
        description=plan["description"],
        payload=f"{plan_id}:{telegram_id}",
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"], amount=plan["stars"])],
    )
    return {"ok": True}


@router.get("/{telegram_id}")
async def get_user(telegram_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    user.last_active_at = datetime.now()

    # Оновлюємо streak
    await update_streak(user, db)
    await db.flush()

    # Перевіряємо досягнення
    try:
        from bot import bot
        await check_and_award(user, db, bot)
    except Exception as e:
        print(f"achievements error: {e}")

    await db.commit()

    return await _user_response(user, db)


async def _user_response(user: User, db: AsyncSession) -> dict:
    referral_count = user.referral_count or 0

    if referral_count < 2:
        next_reward = {"at": 2, "desc": "+10 безкоштовних аналізів", "left": 2 - referral_count}
    elif referral_count < 5:
        next_reward = {"at": 5, "desc": "Love Pro на тиждень", "left": 5 - referral_count}
    elif referral_count < 10:
        next_reward = {"at": 10, "desc": "VIP на 2 тижні", "left": 10 - referral_count}
    else:
        next_reward = None

    outfit_used = await db.scalar(
        select(func.count()).select_from(OutfitAnalysis).where(
            OutfitAnalysis.user_id == user.id
        )
    ) or 0

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "is_premium": user.is_premium,
        "free_analyses_used": user.free_analyses_used,
        "bonus_analyses": user.bonus_analyses or 0,
        "bonus_outfit_analyses": int(user.bonus_outfit_analyses or 0),
        "free_responses_used": int(user.free_responses_used or 0),
        "referral_code": user.referral_code,
        "referral_link": f"https://t.me/flagai_bot?start={user.referral_code}",
        "referral_count": referral_count,
        "next_reward": next_reward,
        "outfit_analyses_used": outfit_used,
        "streak_days": int(user.streak_days or 0),
        "achievements": user.achievements or [],
        "total_analyses": int(user.total_analyses or 0),
        "total_red_flags": int(user.total_red_flags or 0),
        "total_messages": int(user.total_messages or 0),
    }