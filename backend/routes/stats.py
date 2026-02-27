from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database import get_db
from models import User, Analysis, Conversation, Subscription, OutfitAnalysis
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/stats", tags=["stats"])

STATS_PASSWORD = os.getenv("STATS_PASSWORD", "Stats1488!@#")

@router.get("/{password}")
async def get_stats(password: str, db: AsyncSession = Depends(get_db)):
    if password != STATS_PASSWORD:
        raise HTTPException(status_code=403, detail="Невірний пароль")

    total_users = await db.scalar(select(func.count()).select_from(User))

    referred_users = await db.scalar(
        select(func.count()).select_from(User).where(User.referred_by != None)
    )

    top_referrers_result = await db.execute(
        select(User.username, User.telegram_id, User.referral_count)
        .where(User.referral_count >= 2)
        .order_by(User.referral_count.desc())
        .limit(10)
    )
    top_referrers = [
        {"username": r.username or r.telegram_id, "count": r.referral_count}
        for r in top_referrers_result.all()
    ]

    premium_users = await db.scalar(
        select(func.count()).select_from(User).where(User.is_premium == True)
    )

    active_subs = await db.scalar(
        select(func.count()).select_from(Subscription).where(
            and_(
                Subscription.status == "active",
                Subscription.ends_at > datetime.now()
            )
        )
    )

    subs_result = await db.execute(
        select(Subscription.payment_type, func.count().label("count"))
        .where(Subscription.status == "active")
        .group_by(Subscription.payment_type)
    )
    subs_by_type = {r.payment_type: r.count for r in subs_result.all()}

    total_analyses = await db.scalar(select(func.count()).select_from(Analysis))

    chats_result = await db.execute(
        select(Conversation.mode, func.count().label("count"))
        .group_by(Conversation.mode)
    )
    chats_by_mode = {r.mode: r.count for r in chats_result.all()}
    total_chats = sum(chats_by_mode.values())

    total_outfit = await db.scalar(select(func.count()).select_from(OutfitAnalysis))

    week_ago = datetime.now() - timedelta(days=7)
    new_users_week = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= week_ago)
    )

    return {
        "users": {
            "total": total_users,
            "new_this_week": new_users_week,
            "premium": premium_users,
            "referred": referred_users,
        },
        "subscriptions": {
            "active": active_subs,
            "by_type": subs_by_type,
        },
        "activity": {
            "analyses": total_analyses,
            "chats_total": total_chats,
            "chats_by_mode": chats_by_mode,
            "outfit_analyses": total_outfit or 0,
        },
        "referrals": {
            "top_referrers": top_referrers,
        }
    }
