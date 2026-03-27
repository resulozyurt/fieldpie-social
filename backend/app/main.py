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
from backend.app.modules.brand_module import load_brand_context
from backend.app.modules.calendar_module import generate_content_calendar
from backend.app.modules.content_module import generate_content_for_item
from backend.app.database import engine, get_db, Base
from backend.app.models import Calendar, ContentItem

# FastAPI ayağa kalkarken tablolar yoksa veritabanında otomatik oluşturur
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FieldPie Social Media API", version="1.1.0")

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

# Frontend statik dosyalarını (JS/CSS) doğru MIME type ile sunmak için (BEYAZ EKRAN ÇÖZÜMÜ):
UI_ASSETS_DIR = BASE_DIR / "frontend" / "dist" / "ui-assets"
if UI_ASSETS_DIR.exists():
    app.mount("/ui-assets", StaticFiles(directory=str(UI_ASSETS_DIR)), name="ui-assets")

# ---------- helper ----------
def map_item_to_dict(item: ContentItem) -> dict:
    """SQLAlchemy modelini React Frontend'in beklediği dict formatına çevirir."""
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


# ---------- request models ----------

class GenerateCalendarRequest(BaseModel):
    month: int
    year: int

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

@app.get("/")
async def root():
    """Serve React frontend index.html."""
    index = BASE_DIR / "frontend" / "dist" / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"status": "ok", "service": "FieldPie Social Media API", "version": "1.1.0"}


@app.get("/api/brand")
def get_brand():
    try:
        return load_brand_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendars")
def list_calendars(db: Session = Depends(get_db)):
    calendars = db.query(Calendar).order_by(Calendar.year.desc(), Calendar.month.desc()).all()
    result = []
    
    for cal in calendars:
        total = len(cal.items)
        approved = sum(1 for i in cal.items if i.status == "approved")
        generated = sum(1 for i in cal.items if i.status == "content_generated")
        
        result.append({
            "month": cal.month_name,
            "filename": f"db_{cal.month}_{cal.year}", # Frontend uyumluluğu
            "total_items": total,
            "approved": approved,
            "content_generated": generated,
            "pending": total - approved - generated,
        })
    return {"calendars": result}


@app.get("/api/calendar/{year}/{month}")
def get_calendar(year: int, month: int, db: Session = Depends(get_db)):
    cal = db.query(Calendar).filter(Calendar.year == year, Calendar.month == month).first()
    if not cal:
        raise HTTPException(status_code=404, detail=f"Calendar for {month}/{year} not found")
    
    return {
        "month": cal.month_name,
        "total_items": len(cal.items),
        "items": [map_item_to_dict(item) for item in cal.items]
    }


@app.delete("/api/calendar/{year}/{month}")
def delete_calendar(year: int, month: int, db: Session = Depends(get_db)):
    """Mevcut bir takvimi ve tüm içeriklerini veritabanından kalıcı olarak siler."""
    cal = db.query(Calendar).filter(Calendar.year == year, Calendar.month == month).first()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")
    db.delete(cal)
    db.commit()
    return {"success": True}


@app.post("/api/calendar/generate")
def generate_calendar(req: GenerateCalendarRequest, db: Session = Depends(get_db)):
    existing = db.query(Calendar).filter(Calendar.month == req.month, Calendar.year == req.year).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Calendar for {req.month}/{req.year} already exists.")
    try:
        # LLM'den dict olarak ham veri gelir
        calendar_data = generate_content_calendar(month=req.month, year=req.year)
        
        new_cal = Calendar(
            month_name=calendar_data["month"],
            month=req.month,
            year=req.year
        )
        db.add(new_cal)
        db.commit()
        db.refresh(new_cal)

        # Gelen datayı SQL tablolarına basıyoruz
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
    cal = db.query(Calendar).filter(Calendar.month == req.month, Calendar.year == req.year).first()
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")

    try:
        brand_context = load_brand_context()
        success_count = 0
        
        for item in cal.items:
            if item.status == "content_generated":
                continue
                
            # İçerik üreticiye göndermek için dict'e çevir
            item_dict = map_item_to_dict(item)
            try:
                content = generate_content_for_item(item_dict, brand_context)
                item.content_data = content
                item.status = "content_generated"
                item.content_generated_at = datetime.utcnow()
                success_count += 1
            except Exception as e:
                item.status = "error"
                print(f"Error generating content for item {item.id}: {e}")

        db.commit()
        return {"success": True, "generated": success_count, "total": len(cal.items)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/content/regenerate")
def regenerate_item(req: RegenerateContentRequest, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")
        
    try:
        brand_context = load_brand_context()
        new_content = generate_content_for_item(map_item_to_dict(item), brand_context)
        
        item.content_data = new_content
        item.content_generated_at = datetime.utcnow()
        if item.status == "pending" or item.status == "error":
            item.status = "content_generated"
            
        db.commit()
        db.refresh(item)
        return {"success": True, "item": map_item_to_dict(item)}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/item/status")
def update_status(req: UpdateStatusRequest, db: Session = Depends(get_db)):
    valid_statuses = ["pending", "content_generated", "approved", "rejected", "image_generated", "published", "error"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use one of: {valid_statuses}")
        
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")
        
    item.status = req.status
    item.status_updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "item_id": req.item_id, "status": req.status}


@app.patch("/api/item/edit")
def edit_item_field(req: UpdateItemRequest, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")

    editable_top = ["topic", "hook", "notes", "date"]
    editable_content = ["caption", "text_on_image", "description", "image_prompt"]

    if req.field in editable_top:
        setattr(item, req.field, req.value)
    elif req.field in editable_content:
        # JSONB datasını güncellemek için kopyalayıp yeniden atamak gerekir
        data = dict(item.content_data or {})
        data[req.field] = req.value
        item.content_data = data
    else:
        raise HTTPException(status_code=400, detail=f"Field '{req.field}' is not editable")

    item.manually_edited = True
    item.last_edited_at = datetime.utcnow()
    db.commit()
    return {"success": True, "item_id": req.item_id, "field": req.field}


@app.get("/api/item/{year}/{month}/{item_id}")
def get_item(year: int, month: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return map_item_to_dict(item)


@app.get("/api/stats/{year}/{month}")
def get_stats(year: int, month: int, db: Session = Depends(get_db)):
    cal = db.query(Calendar).filter(Calendar.year == year, Calendar.month == month).first()
    if not cal:
        return {"month": "Unknown", "total": 0, "by_status": {}, "by_platform": {}}
        
    statuses = {}
    platforms = {}
    for item in cal.items:
        s = item.status or "pending"
        statuses[s] = statuses.get(s, 0) + 1
        p = item.platform or "Unknown"
        platforms[p] = platforms.get(p, 0) + 1
        
    return {
        "month": cal.month_name,
        "total": len(cal.items),
        "by_status": statuses,
        "by_platform": platforms,
    }


@app.post("/api/image/generate")
def generate_image(req: GenerateImageRequest, db: Session = Depends(get_db)):
    from backend.app.modules.image_module import generate_image_for_item
    item = db.query(ContentItem).filter(ContentItem.id == req.item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")
    if not item.content_data or not item.content_data.get("image_prompt"):
        raise HTTPException(status_code=400, detail="Item has no image_prompt. Generate content first.")
        
    try:
        updated_dict = generate_image_for_item(map_item_to_dict(item))
        
        # Sadece image ile ilgili verileri DB'ye yaz
        item.image_url = updated_dict.get("image_url")
        item.image_generated_at = datetime.utcnow()
        item.image_style_ref_used = updated_dict.get("image_style_ref_used", False)
        item.image_element_used = updated_dict.get("image_element_used", False)
        item.status = updated_dict.get("status", "image_generated")
        
        db.commit()
        db.refresh(item)
        return {"success": True, "item": map_item_to_dict(item)}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/item/image-history/{item_id}")
def get_image_history(item_id: int):
    """Return all previously generated images for an item, newest first."""
    import re as _re
    pattern = _re.compile(rf"^item_{item_id}_\d{{8}}_\d{{6}}\.png$")
    files = sorted(
        [f for f in GENERATED_DIR.iterdir() if pattern.match(f.name)],
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    return {
        "item_id": item_id,
        "images": [
            {
                "url": f"/assets/generated/{f.name}",
                "filename": f.name,
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
            for f in files
        ]
    }

# ---------- Style Reference & Element endpoints ----------
# Bu alanlardaki veriler doğrudan işletim sistemi dosya yapısında saklandığı için değişmedi.

@app.post("/api/item/upload-style")
async def upload_style_reference(item_id: int = Form(...), file: UploadFile = File(...)):
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed: raise HTTPException(status_code=400, detail=f"File type {suffix} not allowed.")
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        old_file = REFERENCES_DIR / f"item_{item_id}_style{ext}"
        if old_file.exists(): old_file.unlink()
    save_path = REFERENCES_DIR / f"item_{item_id}_style{suffix}"
    with open(save_path, "wb") as f: shutil.copyfileobj(file.file, f)
    return {"success": True, "item_id": item_id, "style_url": f"/assets/references/{save_path.name}"}

@app.delete("/api/item/delete-style/{item_id}")
def delete_style_reference(item_id: int):
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = REFERENCES_DIR / f"item_{item_id}_style{ext}"
        if p.exists():
            p.unlink()
            return {"success": True}
    raise HTTPException(status_code=404, detail="No style reference found.")

@app.get("/api/item/style/{item_id}")
def get_style_reference(item_id: int):
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = REFERENCES_DIR / f"item_{item_id}_style{ext}"
        if p.exists(): return {"has_style": True, "style_url": f"/assets/references/{p.name}"}
    return {"has_style": False, "style_url": None}

@app.post("/api/item/upload-element")
async def upload_element(item_id: int = Form(...), file: UploadFile = File(...)):
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed: raise HTTPException(status_code=400, detail=f"File type {suffix} not allowed.")
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        old_file = ELEMENTS_DIR / f"item_{item_id}_element{ext}"
        if old_file.exists(): old_file.unlink()
    save_path = ELEMENTS_DIR / f"item_{item_id}_element{suffix}"
    with open(save_path, "wb") as f: shutil.copyfileobj(file.file, f)
    return {"success": True, "item_id": item_id, "element_url": f"/assets/elements/{save_path.name}"}

@app.delete("/api/item/delete-element/{item_id}")
def delete_element(item_id: int):
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = ELEMENTS_DIR / f"item_{item_id}_element{ext}"
        if p.exists():
            p.unlink()
            return {"success": True}
    raise HTTPException(status_code=404, detail="No design element found.")

@app.get("/api/item/element/{item_id}")
def get_element(item_id: int):
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = ELEMENTS_DIR / f"item_{item_id}_element{ext}"
        if p.exists(): return {"has_element": True, "element_url": f"/assets/elements/{p.name}"}
    return {"has_element": False, "element_url": None}


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve React SPA for all non-API routes."""
    build_dir = BASE_DIR / "frontend" / "dist"
    if not build_dir.exists():
        return {"error": "Frontend not built"}

    file_path = build_dir / full_path

    # İstenen dosya (js, css) klasörde gerçekten varsa onu döndür
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # Dosya yoksa index.html döndür (React Router mantığı)
    return FileResponse(str(build_dir / "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)