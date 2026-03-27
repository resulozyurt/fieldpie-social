from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import sys
import shutil
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import ANTHROPIC_API_KEY, FAL_KEY
from backend.app.modules.calendar_module import generate_content_calendar
from backend.app.modules.content_module import generate_content_for_item
from backend.app.database import engine, get_db, Base
from backend.app.models import Calendar, ContentItem, Brand

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FieldPie Social Media API", version="1.2.0")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
if RAILWAY_URL:
    ALLOWED_ORIGINS.append(f"https://{RAILWAY_URL}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
GENERATED_DIR = ASSETS_DIR / "generated"
REFERENCES_DIR = ASSETS_DIR / "references"
ELEMENTS_DIR = ASSETS_DIR / "elements"

GENERATED_DIR.mkdir(parents=True, exist_ok=True)
REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
ELEMENTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

UI_ASSETS_DIR = BASE_DIR / "frontend" / "dist" / "ui-assets"
if UI_ASSETS_DIR.exists():
    app.mount("/ui-assets", StaticFiles(directory=str(UI_ASSETS_DIR)), name="ui-assets")

# ---------- helper ----------
def map_item_to_dict(item: ContentItem) -> dict:
    return {
        "id": item.id,
        "date": item.date,
        "platform": item.platform,
        "content_pillar": item.content_pillar,
        "format": item.format,
        "topic": item.topic,
        "hook": item.hook,
        "notes": item.notes,
        "status": item.status,
        "content": item.content_data or {},
        "image_url": item.image_url,
        "image_generated_at": item.image_generated_at.isoformat() if item.image_generated_at else None,
        "image_style_ref_used": item.image_style_ref_used,
        "image_element_used": item.image_element_used
    }

def get_brand_context_from_db(brand: Brand):
    """Markanın kimliğini veritabanından çekip AI modüllerine uygun sözlük (dict) haline getirir."""
    return {
        "brand": brand.brand_details or {"name": brand.name},
        "visual_identity": brand.visual_identity or {},
        "social_media": brand.social_media or {}
    }

# ---------- request models ----------

class BrandCreateRequest(BaseModel):
    name: str
    brand_details: dict = {}
    visual_identity: dict = {}
    social_media: dict = {}

class GenerateCalendarRequest(BaseModel):
    month: int
    year: int
    brand_id: int

class UpdateItemRequest(BaseModel):
    month: int
    year: int
    item_id: int
    field: str
    value: str

class UpdateStatusRequest(BaseModel):
    month: int
    year: int
    item_id: int
    status: str

class RegenerateContentRequest(BaseModel):
    month: int
    year: int
    item_id: int

class GenerateImageRequest(BaseModel):
    month: int
    year: int
    item_id: int


# ---------- routes ----------

@app.get("/api/brands")
def get_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).all()
    return [{"id": b.id, "name": b.name} for b in brands]

@app.post("/api/brands")
def create_brand(req: BrandCreateRequest, db: Session = Depends(get_db)):
    new_brand = Brand(name=req.name, brand_details=req.brand_details, visual_identity=req.visual_identity, social_media=req.social_media)
    db.add(new_brand)
    db.commit()
    db.refresh(new_brand)
    return {"success": True, "brand_id": new_brand.id, "name": new_brand.name}

@app.get("/api/calendars")
def list_calendars(brand_id: int, db: Session = Depends(get_db)):
    calendars = db.query(Calendar).filter(Calendar.brand_id == brand_id).order_by(Calendar.year.desc(), Calendar.month.desc()).all()
    result = []
    for cal in calendars:
        total = len(cal.items)
        approved = sum(1 for i in cal.items if i.status == "approved")
        generated = sum(1 for i in cal.items if i.status == "content_generated")
        result.append({
            "month": cal.month_name,
            "filename": f"db_{cal.month}_{cal.year}", 
            "total_items": total,
            "approved": approved,
            "content_generated": generated,
            "pending": total - approved - generated,
        })
    return {"calendars": result}

@app.get("/api/calendar/{year}/{month}")
def get_calendar(year: int, month: int, brand_id: int, db: Session = Depends(get_db)):
    cal = db.query(Calendar).filter(Calendar.year == year, Calendar.month == month, Calendar.brand_id == brand_id).first()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return {
        "month": cal.month_name,
        "total_items": len(cal.items),
        "items": [map_item_to_dict(item) for item in cal.items]
    }

@app.delete("/api/calendar/{year}/{month}")
def delete_calendar(year: int, month: int, brand_id: int, db: Session = Depends(get_db)):
    cal = db.query(Calendar).filter(Calendar.year == year, Calendar.month == month, Calendar.brand_id == brand_id).first()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    db.delete(cal)
    db.commit()
    return {"success": True}

@app.post("/api/calendar/generate")
def generate_calendar(req: GenerateCalendarRequest, db: Session = Depends(get_db)):
    existing = db.query(Calendar).filter(Calendar.month == req.month, Calendar.year == req.year, Calendar.brand_id == req.brand_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Calendar already exists.")
    try:
        # Marka verilerini veritabanından çekip takvim üretecine (AI) yolluyoruz!
        brand = db.query(Brand).filter(Brand.id == req.brand_id).first()
        brand_context = get_brand_context_from_db(brand)
        
        calendar_data = generate_content_calendar(month=req.month, year=req.year, brand_context=brand_context)
        
        new_cal = Calendar(
            brand_id=req.brand_id,
            month_name=calendar_data["month"],
            month=req.month,
            year=req.year
        )
        db.add(new_cal)
        db.commit()
        db.refresh(new_cal)

        for i_data in calendar_data["items"]:
            new_item = ContentItem(
                calendar_id=new_cal.id,
                date=i_data.get("date"),
                platform=i_data.get("platform"),
                content_pillar=i_data.get("content_pillar"),
                format=i_data.get("format"),
                topic=i_data.get("topic"),
                hook=i_data.get("hook"),
                notes=i_data.get("notes"),
                status="pending"
            )
            db.add(new_item)
        db.commit()
        return {"success": True, "month": new_cal.month_name, "total_items": len(calendar_data["items"])}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/generate-all")
def generate_all(req: GenerateCalendarRequest, db: Session = Depends(get_db)):
    cal = db.query(Calendar).filter(Calendar.month == req.month, Calendar.year == req.year, Calendar.brand_id == req.brand_id).first()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")

    try:
        # SQL'den dinamik marka detaylarını çektik!
        brand_context = get_brand_context_from_db(cal.brand)
        success_count = 0
        
        for item in cal.items:
            if item.status == "content_generated": continue
            item_dict = map_item_to_dict(item)
            try:
                content = generate_content_for_item(item_dict, brand_context)
                item.content_data = content
                item.status = "content_generated"
                item.content_generated_at = datetime.utcnow()
                success_count += 1
            except Exception as e:
                item.status = "error"

        db.commit()
        return {"success": True, "generated": success_count, "total": len(cal.items)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/regenerate")
def regenerate_item(req: RegenerateContentRequest, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    try:
        # SQL'den dinamik marka detaylarını çektik!
        brand_context = get_brand_context_from_db(item.calendar.brand)
        new_content = generate_content_for_item(map_item_to_dict(item), brand_context)
        
        item.content_data = new_content
        item.content_generated_at = datetime.utcnow()
        if item.status in ["pending", "error"]:
            item.status = "content_generated"
            
        db.commit()
        db.refresh(item)
        return {"success": True, "item": map_item_to_dict(item)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/item/status")
def update_status(req: UpdateStatusRequest, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    item.status = req.status
    item.status_updated_at = datetime.utcnow()
    db.commit()
    return {"success": True}

@app.patch("/api/item/edit")
def edit_item_field(req: UpdateItemRequest, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    editable_top = ["topic", "hook", "notes", "date"]
    editable_content = ["caption", "text_on_image", "description", "image_prompt"]

    if req.field in editable_top:
        setattr(item, req.field, req.value)
    elif req.field in editable_content:
        data = dict(item.content_data or {})
        data[req.field] = req.value
        item.content_data = data

    item.manually_edited = True
    item.last_edited_at = datetime.utcnow()
    db.commit()
    return {"success": True}

@app.get("/api/item/{year}/{month}/{item_id}")
def get_item(year: int, month: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    return map_item_to_dict(item)

@app.get("/api/stats/{year}/{month}")
def get_stats(year: int, month: int, brand_id: int, db: Session = Depends(get_db)):
    cal = db.query(Calendar).filter(Calendar.year == year, Calendar.month == month, Calendar.brand_id == brand_id).first()
    if not cal: return {"month": "Unknown", "total": 0, "by_status": {}, "by_platform": {}}
    statuses, platforms = {}, {}
    for item in cal.items:
        statuses[item.status or "pending"] = statuses.get(item.status or "pending", 0) + 1
        platforms[item.platform or "Unknown"] = platforms.get(item.platform or "Unknown", 0) + 1
    return {"month": cal.month_name, "total": len(cal.items), "by_status": statuses, "by_platform": platforms}

@app.post("/api/image/generate")
def generate_image(req: GenerateImageRequest, db: Session = Depends(get_db)):
    from backend.app.modules.image_module import generate_image_for_item
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    try:
        updated_dict = generate_image_for_item(map_item_to_dict(item))
        item.image_url = updated_dict.get("image_url")
        item.image_generated_at = datetime.utcnow()
        item.status = updated_dict.get("status", "image_generated")
        db.commit()
        db.refresh(item)
        return {"success": True, "item": map_item_to_dict(item)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/item/image-history/{item_id}")
def get_image_history(item_id: int):
    import re as _re
    pattern = _re.compile(rf"^item_{item_id}_\d{{8}}_\d{{6}}\.png$")
    files = sorted([f for f in GENERATED_DIR.iterdir() if pattern.match(f.name)], key=lambda f: f.stat().st_mtime, reverse=True)
    return {"item_id": item_id, "images": [{"url": f"/assets/generated/{f.name}", "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()} for f in files]}

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    build_dir = BASE_DIR / "frontend" / "dist"
    file_path = build_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    return FileResponse(str(build_dir / "index.html"))

@app.get("/api/dev/init-db")
def init_database(db: Session = Depends(get_db)):
    import json
    from backend.app.models import Brand
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    brand_path = BASE_DIR / "backend" / "app" / "data" / "brand_context.json"
    if brand_path.exists():
        with open(brand_path, "r", encoding="utf-8") as f: data = json.load(f)
        db.add(Brand(name=data["brand"]["name"], brand_details=data["brand"], visual_identity=data["visual_identity"], social_media=data["social_media"]))
        db.commit()
        return {"success": True}
    return {"success": False}