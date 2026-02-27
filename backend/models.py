from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    free_analyses_used = Column(Integer, default=0)
    bonus_analyses = Column(Integer, default=0)
    referral_code = Column(String, unique=True, nullable=True)
    referred_by = Column(Integer, nullable=True)
    referral_count = Column(Integer, default=0)
    analyses_reset_at = Column(DateTime, nullable=True)  # коли останній раз скидались
    created_at = Column(DateTime, server_default=func.now())

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    contact_id = Column(Integer, nullable=True)
    screenshots = Column(JSON)
    context = Column(String, nullable=True)
    interest_level = Column(Float, nullable=True)
    tone = Column(String, nullable=True)
    red_flags = Column(JSON, nullable=True)
    summary = Column(String, nullable=True)
    user_style = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    mode = Column(String, nullable=False)
    messages = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())

class OutfitAnalysis(Base):
    __tablename__ = "outfit_analyses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    status = Column(String, default="inactive")
    started_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    payment_type = Column(String, nullable=True)
