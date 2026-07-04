from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    """Профиль пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)  # НОВОЕ: Имя пользователя
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    activity = Column(Float, nullable=True)
    goal = Column(String, nullable=True)
    daily_calories = Column(Float, nullable=True)
    daily_proteins = Column(Float, nullable=True)
    daily_fats = Column(Float, nullable=True)
    daily_carbs = Column(Float, nullable=True)
    onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GlobalProduct(Base):
    __tablename__ = "global_products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    calories = Column(Float, nullable=False)
    proteins = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)

class UserProduct(Base):
    __tablename__ = "user_products"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    proteins = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyLog(Base):
    __tablename__ = "daily_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    product_name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)
    proteins = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)