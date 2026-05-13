from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from database import get_db
from models import User, Analysis, Contact, Subscription, OutfitAnalysis
from services.openai_service import analyze_screenshots, analyze_outfit, compare_crushes
from typing import List
import base64
from datetime import datetime, timedelta

router = APIRouter(prefix="/analyze", tags=["analyze"])

FREE_ANALYSES_LIMIT = 5
LOVE_PRO_ANALYSES_LIMIT = 50

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


async def check_and_reset_analyses(user: User, plan: str, db: AsyncSession):
    try:
        now = datetime.now()
        reset_at = user.analyses_reset_at or user.created_at or now
        period = timedelta(weeks=1) if plan == "free" else timedelta(days=30)
        if (now - reset_at) >= period:
            user.free_analyses_used = 0
            user.analyses_reset_at = now
            await db.flush()
            print(f"RESET analyses for {user.telegram_id} plan={plan}")
    except Exception as e:
        print(f"RESET ERROR: {e}")


@router.post("/")
async def analyze(
    telegram_id: str = Form(...),
    context: str = Form(None),
    crush_name: str = Form(None),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    plan = await get_plan(user, db)
    await check_and_reset_analyses(user, plan, db)

    if plan == "free":
        limit = FREE_ANALYSES_LIMIT + (user.bonus_analyses or 0)
        if user.free_analyses_used >= limit:
            raise HTTPException(
                status_code=403,
                detail="UPGRADE_REQUIRED:Ліміт 3 безкоштовних аналізів вичерпано. Оформи Love Pro 💜 для 50 аналізів на місяць"
            )
    elif plan == "love_pro":
        if user.free_analyses_used >= LOVE_PRO_ANALYSES_LIMIT:
            raise HTTPException(
                status_code=403,
                detail="UPGRADE_REQUIRED:Ліміт 50 аналізів на місяць вичерпано. Переходь на VIP 👑 для безліміту"
            )

    contact_id = None
    if crush_name and crush_name.strip():
        contact_result = await db.execute(
            select(Contact).where(
                and_(
                    Contact.user_id == user.id,
                    Contact.name == crush_name.strip()
                )
            )
        )
        contact = contact_result.scalar_one_or_none()
        if not contact:
            contact = Contact(user_id=user.id, name=crush_name.strip())
            db.add(contact)
            await db.flush()
        contact_id = contact.id

    screenshot_b64_list = []
    for file in files:
        contents = await file.read()
        encoded = base64.b64encode(contents).decode("utf-8")
        screenshot_b64_list.append(f"data:image/jpeg;base64,{encoded}")

    analysis_result = await analyze_screenshots(screenshot_b64_list, context)
    if "error" in analysis_result:
        raise HTTPException(status_code=500, detail=analysis_result["error"])

    analysis = Analysis(
        user_id=user.id,
        contact_id=contact_id,
        screenshots=[],
        context=context,
        interest_level=analysis_result.get("interest_level"),
        tone=analysis_result.get("tone"),
        red_flags=analysis_result.get("red_flags", []),
        summary=analysis_result.get("summary"),
        user_style=analysis_result.get("user_style")
    )
    db.add(analysis)

    if plan != "vip":
        user.free_analyses_used += 1

    await db.commit()
    await db.refresh(analysis)

    free_left = None
    if plan == "free":
        free_left = max(0, FREE_ANALYSES_LIMIT + (user.bonus_analyses or 0) - user.free_analyses_used)
    elif plan == "love_pro":
        free_left = max(0, LOVE_PRO_ANALYSES_LIMIT - user.free_analyses_used)

    return {
        "analysis_id": analysis.id,
        "crush_name": crush_name,
        "interest_level": analysis.interest_level,
        "vibe_check": analysis_result.get("vibe_check"),
        "tone": analysis.tone,
        "response_pattern": analysis_result.get("response_pattern"),
        "red_flags": analysis.red_flags,
        "summary": analysis.summary,
        "user_style": analysis.user_style,
        "free_analyses_left": free_left,
        "plan": plan
    }


@router.get("/history/{telegram_id}")
async def get_history(telegram_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    analyses = await db.execute(
        select(Analysis).where(Analysis.user_id == user.id).order_by(Analysis.created_at.desc())
    )
    return [
        {
            "id": a.id,
            "contact_id": a.contact_id,
            "interest_level": a.interest_level,
            "tone": a.tone,
            "summary": a.summary,
            "created_at": str(a.created_at)
        }
        for a in analyses.scalars().all()
    ]


@router.get("/crushes/{telegram_id}")
async def get_crushes(telegram_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    plan = await get_plan(user, db)
    if plan == "free":
        raise HTTPException(
            status_code=403,
            detail="UPGRADE_REQUIRED:Картотека крашів доступна в Love Pro 💜 або VIP 👑"
        )

    contacts_result = await db.execute(
        select(Contact).where(Contact.user_id == user.id)
    )
    contacts = contacts_result.scalars().all()

    crushes = []
    for contact in contacts:
        analyses_result = await db.execute(
            select(Analysis).where(
                and_(
                    Analysis.user_id == user.id,
                    Analysis.contact_id == contact.id
                )
            ).order_by(Analysis.created_at.asc())
        )
        analyses = analyses_result.scalars().all()
        if not analyses:
            continue

        avg_interest = sum(a.interest_level for a in analyses if a.interest_level) / len(analyses)
        crushes.append({
            "contact_id": contact.id,
            "name": contact.name,
            "avg_interest": round(avg_interest, 1),
            "analyses_count": len(analyses),
            "last_analysis": {
                "id": analyses[-1].id,
                "interest_level": analyses[-1].interest_level,
                "tone": analyses[-1].tone,
                "summary": analyses[-1].summary,
                "created_at": str(analyses[-1].created_at)
            },
            "history": [
                {"interest_level": a.interest_level, "tone": a.tone, "created_at": str(a.created_at)}
                for a in analyses
            ]
        })

    return crushes


@router.post("/compare")
async def compare(
    telegram_id: str = Form(...),
    crush1_id: int = Form(...),
    crush2_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    plan = await get_plan(user, db)
    if plan == "free":
        raise HTTPException(
            status_code=403,
            detail="UPGRADE_REQUIRED:Порівняння крашів доступне в Love Pro 💜 або VIP 👑"
        )

    async def get_crush_data(contact_id: int):
        contact_result = await db.execute(select(Contact).where(Contact.id == contact_id))
        contact = contact_result.scalar_one_or_none()
        if not contact:
            return None
        analyses_result = await db.execute(
            select(Analysis).where(
                and_(Analysis.user_id == user.id, Analysis.contact_id == contact_id)
            )
        )
        analyses = analyses_result.scalars().all()
        avg_interest = sum(a.interest_level for a in analyses if a.interest_level) / len(analyses) if analyses else 0
        all_red_flags = []
        for a in analyses:
            if a.red_flags:
                for flag in a.red_flags:
                    all_red_flags.append(flag.get("flag", "") if isinstance(flag, dict) else flag)
        return {
            "name": contact.name,
            "avg_interest": round(avg_interest, 1),
            "tones": [a.tone for a in analyses if a.tone],
            "red_flags": list(set(all_red_flags))
        }

    crush1_data = await get_crush_data(crush1_id)
    crush2_data = await get_crush_data(crush2_id)
    if not crush1_data or not crush2_data:
        raise HTTPException(status_code=404, detail="Краша не знайдено")

    return await compare_crushes(crush1_data, crush2_data)


@router.post("/outfit")
async def analyze_outfit_route(
    telegram_id: str = Form(...),
    destination: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    plan = await get_plan(user, db)

    if plan == "free":
        outfit_count = await db.scalar(
            select(func.count()).select_from(OutfitAnalysis).where(
                OutfitAnalysis.user_id == user.id
            )
        )
        if outfit_count >= 2:
            raise HTTPException(
                status_code=403,
                detail="UPGRADE_REQUIRED:Безкоштовні спроби стиліста вичерпано (2/2). Отримай VIP 👑 для безліміту"
            )

    contents = await file.read()
    image_data = base64.b64encode(contents).decode("utf-8")
    result = await analyze_outfit(image_data, destination)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    outfit_log = OutfitAnalysis(user_id=user.id)
    db.add(outfit_log)
    await db.commit()

    return result
