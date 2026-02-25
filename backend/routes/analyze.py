from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from database import get_db
from models import User, Analysis, Contact
from services.openai_service import analyze_screenshots, analyze_outfit, compare_crushes
from typing import List, Optional
import base64

router = APIRouter(prefix="/analyze", tags=["analyze"])

FREE_ANALYSES_LIMIT = 3  # збільшено для тестування

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

    if not user.is_premium and user.free_analyses_used >= (FREE_ANALYSES_LIMIT + (user.bonus_analyses or 0)):
        raise HTTPException(status_code=403, detail="Ліміт безкоштовних аналізів вичерпано. Оформи підписку.")

    # Знаходимо або створюємо контакт — ОДИН контакт на ім'я
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

    if not user.is_premium:
        user.free_analyses_used += 1

    await db.commit()
    await db.refresh(analysis)

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
        "free_analyses_left": max(0, FREE_ANALYSES_LIMIT + (user.bonus_analyses or 0) - user.free_analyses_used) if not user.is_premium else None
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
    analyses = analyses.scalars().all()

    return [
        {
            "id": a.id,
            "contact_id": a.contact_id,
            "interest_level": a.interest_level,
            "tone": a.tone,
            "summary": a.summary,
            "created_at": str(a.created_at)
        }
        for a in analyses
    ]


@router.get("/crushes/{telegram_id}")
async def get_crushes(telegram_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

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
                {
                    "interest_level": a.interest_level,
                    "tone": a.tone,
                    "created_at": str(a.created_at)
                }
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

    async def get_crush_data(contact_id: int):
        contact_result = await db.execute(select(Contact).where(Contact.id == contact_id))
        contact = contact_result.scalar_one_or_none()
        if not contact:
            return None

        analyses_result = await db.execute(
            select(Analysis).where(
                and_(
                    Analysis.user_id == user.id,
                    Analysis.contact_id == contact_id
                )
            )
        )
        analyses = analyses_result.scalars().all()

        avg_interest = sum(a.interest_level for a in analyses if a.interest_level) / len(analyses) if analyses else 0
        tones = [a.tone for a in analyses if a.tone]
        all_red_flags = []
        for a in analyses:
            if a.red_flags:
                for flag in a.red_flags:
                    if isinstance(flag, dict):
                        all_red_flags.append(flag.get("flag", ""))
                    else:
                        all_red_flags.append(flag)

        return {
            "name": contact.name,
            "avg_interest": round(avg_interest, 1),
            "tones": tones,
            "red_flags": list(set(all_red_flags))
        }

    crush1_data = await get_crush_data(crush1_id)
    crush2_data = await get_crush_data(crush2_id)

    if not crush1_data or not crush2_data:
        raise HTTPException(status_code=404, detail="Краша не знайдено")

    comparison = await compare_crushes(crush1_data, crush2_data)
    return comparison


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

    contents = await file.read()
    image_data = base64.b64encode(contents).decode("utf-8")

    result = await analyze_outfit(image_data, destination)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result