from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB # PostgreSQL'in süper hızlı JSON veri tipi
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Calendar(Base):
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    month_name = Column(String, index=True) # Örn: "March 2026"
    month = Column(Integer)
    year = Column(Integer)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Bir takvimin birden fazla içeriği olur (One-to-Many ilişkisi)
    items = relationship("ContentItem", back_populates="calendar", cascade="all, delete-orphan")


class ContentItem(Base):
    __tablename__ = "content_items"
    
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id", ondelete="CASCADE"))
    
    # Temel Post Bilgileri
    date = Column(String) # YYYY-MM-DD
    platform = Column(String)
    content_pillar = Column(String)
    format = Column(String)
    topic = Column(String)
    hook = Column(String)
    notes = Column(Text)
    status = Column(String, default="pending")
    
    # Yapay zekanın ürettiği içerikler (PostgreSQL JSONB ile mükemmel çalışır)
    content_data = Column(JSONB, nullable=True) # caption, image_prompt, text_on_image vs.
    
    # Loglama ve Zaman Damgaları
    content_generated_at = Column(DateTime, nullable=True)
    status_updated_at = Column(DateTime, nullable=True)
    last_edited_at = Column(DateTime, nullable=True)
    manually_edited = Column(Boolean, default=False)
    
    # Görsel Bilgileri
    image_url = Column(String, nullable=True)
    image_generated_at = Column(DateTime, nullable=True)
    image_style_ref_used = Column(Boolean, default=False)
    image_element_used = Column(Boolean, default=False)

    calendar = relationship("Calendar", back_populates="items")