from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, DateTime
from database import get_db
from models import User, Analysis, Conversation, Subscription, OutfitAnalysis
from datetime import datetime, timedelta
from typing import Optional
import os

router = APIRouter(prefix="/stats", tags=["stats"])

STATS_TOKEN = os.getenv("STATS_PASSWORD", "Stats1488")

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Unauthorized")
    token = authorization.replace("Bearer ", "")
    if token != STATS_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return token


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = await db.scalar(select(func.count()).select_from(User)) or 0
    new_today = await db.scalar(select(func.count()).select_from(User).where(User.created_at >= today)) or 0
    new_week = await db.scalar(select(func.count()).select_from(User).where(User.created_at >= week_ago)) or 0
    new_month = await db.scalar(select(func.count()).select_from(User).where(User.created_at >= month_ago)) or 0
dau = await db.scalar(
select(func.count())
.select_from(User)
.where(
cast(User.last_active_at, DateTime) >= today
)
) or 0

wau = await db.scalar(
select(func.count())
.select_from(User)
.where(
cast(User.last_active_at, DateTime) >= week_ago
)
) or 0

mau = await db.scalar(
select(func.count())
.select_from(User)
.where(
cast(User.last_active_at, DateTime) >= month_ago
)
) or 0

    stickiness = round(dau / mau * 100, 1) if mau else 0
    premium_users = await db.scalar(select(func.count()).select_from(User).where(User.is_premium == True)) or 0
    referred_users = await db.scalar(select(func.count()).select_from(User).where(User.referred_by != None)) or 0

    active_subs = await db.scalar(
        select(func.count()).select_from(Subscription).where(
            and_(Subscription.status == "active", Subscription.ends_at > now)
        )
    ) or 0

    return {
        "total_users": total_users,
        "new_today": new_today,
        "new_week": new_week,
        "new_month": new_month,
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "stickiness": stickiness,
        "premium_users": premium_users,
        "referred_users": referred_users,
        "active_subs": active_subs,
    }


@router.get("/revenue")
async def get_revenue(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    now = datetime.now()
    month_ago = now - timedelta(days=30)

    PLAN_PRICES = {
        "stars_love_pro": 100,
        "stars_vip": 250,
    }

    subs_result = await db.execute(
        select(Subscription.payment_type, func.count().label("count"))
        .where(and_(Subscription.status == "active", Subscription.ends_at > now))
        .group_by(Subscription.payment_type)
    )
    subs_by_type = {r.payment_type: r.count for r in subs_result.all()}

    mrr_stars = sum(PLAN_PRICES.get(pt, 0) * count for pt, count in subs_by_type.items())

    total_users = await db.scalar(select(func.count()).select_from(User)) or 1
    premium_users = await db.scalar(select(func.count()).select_from(User).where(User.is_premium == True)) or 0

    new_subs_month = await db.scalar(
        select(func.count()).select_from(Subscription).where(
            and_(Subscription.status == "active", Subscription.started_at >= month_ago)
        )
    ) or 0

    conversion_rate = round(premium_users / total_users * 100, 1) if total_users else 0
    arpu = round(mrr_stars / total_users, 1) if total_users else 0
    arppu = round(mrr_stars / premium_users, 1) if premium_users else 0

    return {
        "mrr_stars": mrr_stars,
        "arr_stars": mrr_stars * 12,
        "arpu_stars": arpu,
        "arppu_stars": arppu,
        "conversion_rate": conversion_rate,
        "new_subs_month": new_subs_month,
        "subs_by_type": subs_by_type,
    }


@router.get("/retention")
async def get_retention(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    now = datetime.now()

    yesterday = now - timedelta(days=1)
    day_before = now - timedelta(days=2)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    month_ago = now - timedelta(days=30)
    two_months_ago = now - timedelta(days=60)

    async def retention_rate(reg_from, reg_to, active_from):
        total = await db.scalar(
            select(func.count()).select_from(User).where(
                and_(User.created_at >= reg_from, User.created_at < reg_to)
            )
        ) or 0
        returned = await db.scalar(
            select(func.count()).select_from(User).where(
                and_(
                    User.created_at >= reg_from,
                    User.created_at < reg_to,
                    User.last_active_at >= active_from
                )
            )
        ) or 0
        rate = round(returned / total * 100, 1) if total else 0
        return {"total": total, "returned": returned, "rate": rate}

    d1 = await retention_rate(day_before, yesterday, yesterday)
    d7 = await retention_rate(two_weeks_ago, week_ago, week_ago)
    d30 = await retention_rate(two_months_ago, month_ago, month_ago)

    # Середній streak — без cast
    streak_result = await db.execute(
        select(func.avg(User.streak_days))
        .select_from(User)
        .where(User.streak_days != None)
    )
    avg_streak = round(float(streak_result.scalar() or 0), 1)

    # Юзери з streak > 0 — без cast
    active_streak = await db.scalar(
        select(func.count()).select_from(User).where(
            and_(User.streak_days != None, User.streak_days > 0)
        )
    ) or 0

    return {
        "d1": d1,
        "d7": d7,
        "d30": d30,
        "avg_streak": avg_streak,
        "active_streak_users": active_streak,
    }


@router.get("/funnel")
async def get_funnel(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    total_users = await db.scalar(select(func.count()).select_from(User)) or 1

    did_analysis = await db.scalar(
        select(func.count(func.distinct(Analysis.user_id))).select_from(Analysis)
    ) or 0

    did_chat = await db.scalar(
        select(func.count(func.distinct(Conversation.user_id))).select_from(Conversation)
    ) or 0

    did_outfit = await db.scalar(
        select(func.count(func.distinct(OutfitAnalysis.user_id))).select_from(OutfitAnalysis)
    ) or 0

    did_premium = await db.scalar(
        select(func.count(func.distinct(Subscription.user_id))).select_from(Subscription)
    ) or 0

    def pct(n):
        return round(n / total_users * 100, 1)

    return {
        "steps": [
            {"name": "Зареєструвались", "count": total_users, "pct": 100},
            {"name": "Зробили аналіз", "count": did_analysis, "pct": pct(did_analysis)},
            {"name": "Написали в чат", "count": did_chat, "pct": pct(did_chat)},
            {"name": "Спробували стиліст", "count": did_outfit, "pct": pct(did_outfit)},
            {"name": "Купили підписку", "count": did_premium, "pct": pct(did_premium)},
        ]
    }


@router.get("/activity")
async def get_activity(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    total_analyses = await db.scalar(select(func.count()).select_from(Analysis)) or 0
    week_analyses = await db.scalar(
        select(func.count()).select_from(Analysis).where(Analysis.created_at >= week_ago)
    ) or 0

    chats_result = await db.execute(
        select(Conversation.mode, func.count().label("count"))
        .group_by(Conversation.mode)
    )
    chats_by_mode = {r.mode: r.count for r in chats_result.all()}
    total_chats = sum(chats_by_mode.values())

    total_outfit = await db.scalar(select(func.count()).select_from(OutfitAnalysis)) or 0

    daily_result = await db.execute(
        select(
            func.extract('dow', Analysis.created_at).label('dow'),
            func.count().label('count')
        )
        .where(Analysis.created_at >= week_ago)
        .group_by(func.extract('dow', Analysis.created_at))
    )
    daily = {int(r.dow): r.count for r in daily_result.all()}
    days = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
    daily_chart = [{"day": days[i], "count": daily.get(i, 0)} for i in range(7)]

    return {
        "total_analyses": total_analyses,
        "week_analyses": week_analyses,
        "total_chats": total_chats,
        "chats_by_mode": chats_by_mode,
        "outfit_analyses": total_outfit,
        "daily_chart": daily_chart,
    }


@router.get("/growth")
async def get_growth(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    now = datetime.now()

    days_data = []
    for i in range(29, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = await db.scalar(
            select(func.count()).select_from(User).where(
                and_(User.created_at >= day_start, User.created_at < day_end)
            )
        ) or 0
        days_data.append({"date": day_start.strftime("%d.%m"), "users": count})

    analyses_data = []
    for i in range(29, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = await db.scalar(
            select(func.count()).select_from(Analysis).where(
                and_(Analysis.created_at >= day_start, Analysis.created_at < day_end)
            )
        ) or 0
        analyses_data.append({"date": day_start.strftime("%d.%m"), "analyses": count})

    return {
        "registrations": days_data,
        "analyses": analyses_data,
    }


@router.get("/segments")
async def get_segments(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Power users — без cast
    power_users = await db.scalar(
        select(func.count()).select_from(User).where(
            User.total_analyses >= 10
        )
    ) or 0

    whales = await db.scalar(
        select(func.count()).select_from(Subscription).where(
            and_(
                Subscription.payment_type.like("%vip%"),
                Subscription.status == "active",
                Subscription.ends_at > now
            )
        )
    ) or 0

    churn_risk = await db.scalar(
        select(func.count()).select_from(User).where(
            and_(
                User.last_active_at >= month_ago,
                User.last_active_at < week_ago,
                User.is_premium == True
            )
        )
    ) or 0

    inactive = await db.scalar(
        select(func.count()).select_from(User).where(
            and_(
                User.last_active_at != None,
                User.last_active_at < month_ago
            )
        )
    ) or 0

    new_users = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= week_ago)
    ) or 0

    referral_users = await db.scalar(
        select(func.count()).select_from(User).where(User.referred_by != None)
    ) or 0

    return {
        "power_users": power_users,
        "whales": whales,
        "churn_risk": churn_risk,
        "inactive": inactive,
        "new_users": new_users,
        "referral_users": referral_users,
    }


@router.get("/referrals")
async def get_referrals(db: AsyncSession = Depends(get_db), token: str = Depends(verify_token)):
    total_users = await db.scalar(select(func.count()).select_from(User)) or 1
    referred_users = await db.scalar(
        select(func.count()).select_from(User).where(User.referred_by != None)
    ) or 0

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

    referred_premium = await db.scalar(
        select(func.count()).select_from(User).where(
            and_(User.referred_by != None, User.is_premium == True)
        )
    ) or 0

    referral_conversion = round(referred_premium / referred_users * 100, 1) if referred_users else 0
    viral_coefficient = round(referred_users / total_users, 2)

    return {
        "total_referred": referred_users,
        "referred_premium": referred_premium,
        "referral_conversion": referral_conversion,
        "viral_coefficient": viral_coefficient,
        "top_referrers": top_referrers,
    }


@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_token),
    search: Optional[str] = None,
    limit: int = 20
):
    query = select(User).order_by(User.created_at.desc())
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.telegram_id.ilike(f"%{search}%"))
        )
    query = query.limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "telegram_id": u.telegram_id,
                "username": u.username or "—",
                "is_premium": u.is_premium,
                "free_analyses_used": u.free_analyses_used or 0,
                "total_analyses": int(u.total_analyses or 0),
                "total_messages": int(u.total_messages or 0),
                "referral_count": u.referral_count or 0,
                "streak_days": int(u.streak_days or 0),
                "achievements_count": len(u.achievements) if isinstance(u.achievements, list) else 0,
                "last_active_at": str(u.last_active_at) if u.last_active_at else None,
                "created_at": str(u.created_at) if u.created_at else None,
            }
            for u in users
        ]
    }