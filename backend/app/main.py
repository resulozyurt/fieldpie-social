from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import json
import sys
import shutil
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.config import ANTHROPIC_API_KEY, FAL_KEY
from backend.app.modules.brand_module import load_brand_context, build_brand_system_prompt
from backend.app.modules.calendar_module import generate_content_calendar, save_calendar
from backend.app.modules.content_module import generate_content_for_item, generate_all_content

app = FastAPI(title="FieldPie Social Media API", version="1.0.0")

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
DATA_DIR = BASE_DIR / "backend" / "app" / "data"
ASSETS_DIR = BASE_DIR / "assets"
GENERATED_DIR = ASSETS_DIR / "generated"
REFERENCES_DIR = ASSETS_DIR / "references"
ELEMENTS_DIR = ASSETS_DIR / "elements"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
ELEMENTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Serve React frontend build in production
FRONTEND_BUILD = BASE_DIR / "frontend" / "dist"
if FRONTEND_BUILD.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD / "assets")), name="frontend-assets")


# ---------- helpers ----------

def get_calendar_path(month: int, year: int) -> Path:
    dt = datetime(year, month, 1)
    slug = dt.strftime("%B_%Y").lower()
    return DATA_DIR / f"calendar_{slug}.json"


def load_calendar(month: int, year: int) -> dict:
    path = get_calendar_path(month, year)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Calendar for {month}/{year} not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_calendar_data(data: dict, month: int, year: int):
    path = get_calendar_path(month, year)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_reference_path(item_id: int) -> Path | None:
    """Return path of existing reference image for an item, or None."""
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = REFERENCES_DIR / f"item_{item_id}_ref{ext}"
        if p.exists():
            return p
    return None


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
def root():
    return {"status": "ok", "service": "FieldPie Social Media API", "version": "1.0.0"}


@app.get("/api/brand")
def get_brand():
    try:
        return load_brand_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/{year}/{month}")
def get_calendar(year: int, month: int):
    return load_calendar(month, year)


@app.get("/api/calendars")
def list_calendars():
    files = sorted(DATA_DIR.glob("calendar_*.json"))
    calendars = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        total = len(data.get("items", []))
        approved = sum(1 for i in data["items"] if i.get("status") == "approved")
        generated = sum(1 for i in data["items"] if i.get("status") == "content_generated")
        calendars.append({
            "month": data.get("month"),
            "filename": f.name,
            "total_items": total,
            "approved": approved,
            "content_generated": generated,
            "pending": total - approved - generated,
        })
    return {"calendars": calendars}


@app.post("/api/calendar/generate")
def generate_calendar(req: GenerateCalendarRequest):
    path = get_calendar_path(req.month, req.year)
    if path.exists():
        raise HTTPException(status_code=409, detail=f"Calendar for {req.month}/{req.year} already exists.")
    try:
        calendar_data = generate_content_calendar(month=req.month, year=req.year)
        save_calendar(calendar_data, output_dir=str(DATA_DIR))
        return {"success": True, "month": calendar_data["month"], "total_items": calendar_data["total_items"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/content/generate-all")
def generate_all(req: GenerateCalendarRequest):
    path = get_calendar_path(req.month, req.year)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Calendar not found")
    try:
        calendar_data = generate_all_content(calendar_path=str(path))
        success = sum(1 for i in calendar_data["items"] if i.get("status") == "content_generated")
        return {"success": True, "generated": success, "total": len(calendar_data["items"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/content/regenerate")
def regenerate_item(req: RegenerateContentRequest):
    import traceback
    calendar_data = load_calendar(req.month, req.year)
    item = next((i for i in calendar_data["items"] if i["id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")
    try:
        brand_context = load_brand_context()
        new_content = generate_content_for_item(item, brand_context)
        # Only update content fields — preserve status, image_url, everything else
        item["content"] = new_content
        item["content_regenerated_at"] = datetime.now().isoformat()
        # Upgrade status only if it was still pending
        if item.get("status") == "pending":
            item["status"] = "content_generated"
        save_calendar_data(calendar_data, req.month, req.year)
        return {"success": True, "item": item}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/item/status")
def update_status(req: UpdateStatusRequest):
    valid_statuses = ["pending", "content_generated", "approved", "rejected", "image_generated", "published"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use one of: {valid_statuses}")
    calendar_data = load_calendar(req.month, req.year)
    item = next((i for i in calendar_data["items"] if i["id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")
    item["status"] = req.status
    item["status_updated_at"] = datetime.now().isoformat()
    save_calendar_data(calendar_data, req.month, req.year)
    return {"success": True, "item_id": req.item_id, "status": req.status}


@app.patch("/api/item/edit")
def edit_item_field(req: UpdateItemRequest):
    calendar_data = load_calendar(req.month, req.year)
    item = next((i for i in calendar_data["items"] if i["id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")

    editable_top = ["topic", "hook", "notes"]
    editable_content = ["caption", "text_on_image", "description", "image_prompt"]

    if req.field in editable_top:
        item[req.field] = req.value
    elif req.field in editable_content:
        if "content" not in item:
            raise HTTPException(status_code=400, detail="Content not yet generated for this item")
        item["content"][req.field] = req.value
    else:
        raise HTTPException(status_code=400, detail=f"Field '{req.field}' is not editable")

    item["manually_edited"] = True
    item["last_edited_at"] = datetime.now().isoformat()
    save_calendar_data(calendar_data, req.month, req.year)
    return {"success": True, "item_id": req.item_id, "field": req.field}


@app.get("/api/item/{year}/{month}/{item_id}")
def get_item(year: int, month: int, item_id: int):
    calendar_data = load_calendar(month, year)
    item = next((i for i in calendar_data["items"] if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@app.get("/api/stats/{year}/{month}")
def get_stats(year: int, month: int):
    calendar_data = load_calendar(month, year)
    items = calendar_data["items"]
    statuses = {}
    for item in items:
        s = item.get("status", "pending")
        statuses[s] = statuses.get(s, 0) + 1
    platforms = {}
    for item in items:
        p = item.get("platform", "Unknown")
        platforms[p] = platforms.get(p, 0) + 1
    return {
        "month": calendar_data["month"],
        "total": len(items),
        "by_status": statuses,
        "by_platform": platforms,
    }


@app.post("/api/image/generate")
def generate_image(req: GenerateImageRequest):
    from backend.app.modules.image_module import generate_image_for_item
    calendar_data = load_calendar(req.month, req.year)
    item = next((i for i in calendar_data["items"] if i["id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {req.item_id} not found")
    if not item.get("content", {}).get("image_prompt"):
        raise HTTPException(status_code=400, detail="Item has no image_prompt. Generate content first.")
    try:
        import traceback
        updated_item = generate_image_for_item(item)
        for i, cal_item in enumerate(calendar_data["items"]):
            if cal_item["id"] == req.item_id:
                calendar_data["items"][i] = updated_item
                break
        save_calendar_data(calendar_data, req.month, req.year)
        return {"success": True, "item": updated_item}
    except Exception as e:
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

# ---------- Style Reference endpoints ----------

@app.post("/api/item/upload-style")
async def upload_style_reference(
    item_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload a STYLE reference — Ideogram will match the visual style/mood."""
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {suffix} not allowed.")
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        old_file = REFERENCES_DIR / f"item_{item_id}_style{ext}"
        if old_file.exists():
            old_file.unlink()
    save_path = REFERENCES_DIR / f"item_{item_id}_style{suffix}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
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
        if p.exists():
            return {"has_style": True, "style_url": f"/assets/references/{p.name}"}
    return {"has_style": False, "style_url": None}


# ---------- Design Element endpoints ----------

@app.post("/api/item/upload-element")
async def upload_element(
    item_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload a DESIGN ELEMENT — this image will be used inside the composition (mockup, icon, etc)."""
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {suffix} not allowed.")
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        old_file = ELEMENTS_DIR / f"item_{item_id}_element{ext}"
        if old_file.exists():
            old_file.unlink()
    save_path = ELEMENTS_DIR / f"item_{item_id}_element{suffix}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
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
        if p.exists():
            return {"has_element": True, "element_url": f"/assets/elements/{p.name}"}
    return {"has_element": False, "element_url": None}

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve React SPA for all non-API routes."""
    build_dir = BASE_DIR / "frontend" / "dist"
    if not build_dir.exists():
        return {"error": "Frontend not built"}
    file_path = build_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    return FileResponse(str(build_dir / "index.html"))
