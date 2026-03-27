from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Örn: FieldPie, Evatro
    
    # Marka Kimliği (JSONB ile esnek tutuyoruz, her markanın dinamikleri farklı olabilir)
    brand_details = Column(JSONB, default={}) 
    visual_identity = Column(JSONB, default={})
    social_media = Column(JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    # Bir markanın birden fazla takvimi olabilir (One-to-Many)
    calendars = relationship("Calendar", back_populates="brand", cascade="all, delete-orphan")


class Calendar(Base):
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True) # Takvimi markaya bağladık
    
    month_name = Column(String, index=True)
    month = Column(Integer)
    year = Column(Integer)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    brand = relationship("Brand", back_populates="calendars")
    items = relationship("ContentItem", back_populates="calendar", cascade="all, delete-orphan")


class ContentItem(Base):
    __tablename__ = "content_items"
    
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id", ondelete="CASCADE"))
    
    date = Column(String) 
    platform = Column(String)
    content_pillar = Column(String)
    format = Column(String)
    topic = Column(String)
    hook = Column(String)
    notes = Column(Text)
    status = Column(String, default="pending")
    
    content_data = Column(JSONB, nullable=True) 
    
    content_generated_at = Column(DateTime, nullable=True)
    status_updated_at = Column(DateTime, nullable=True)
    last_edited_at = Column(DateTime, nullable=True)
    manually_edited = Column(Boolean, default=False)
    
    image_url = Column(String, nullable=True)
    image_generated_at = Column(DateTime, nullable=True)
    image_style_ref_used = Column(Boolean, default=False)
    image_element_used = Column(Boolean, default=False)

    calendar = relationship("Calendar", back_populates="items")