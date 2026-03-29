import fal_client
import os
import re
import httpx
import asyncio
import base64
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.config import FAL_KEY
from backend.app.modules.render_module import render_html_to_image, generate_brand_html

os.environ["FAL_KEY"] = FAL_KEY

BASE_DIR = Path(__file__).parent.parent.parent.parent
GENERATED_DIR = BASE_DIR / "assets" / "generated"
REFERENCES_DIR = BASE_DIR / "assets" / "references"
ELEMENTS_DIR = BASE_DIR / "assets" / "elements"

GENERATED_DIR.mkdir(parents=True, exist_ok=True)
REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
ELEMENTS_DIR.mkdir(parents=True, exist_ok=True)

TEXT_INSTRUCTION_PATTERNS = [
    r'text\s+(overlay|reads?|says?|that\s+reads?)[^.]*\.',
    r'(bold\s+)?(white|black|teal|dark)?\s*text\s+["\'][^"\']*["\']',
    r'headline\s+["\'][^"\']*["\']',
    r'(floating|oversized|large)\s+text[^.]*\.',
    r'reads?\s+["\'][^"\']*["\']',
    r'(caption|label|title|tagline)\s+["\'][^"\']*["\']',
    r'(text|words|letters|typography|labels)\b.*?\.',
]

def clean_prompt(prompt: str) -> str:
    prompt = re.sub(r'#[0-9A-Fa-f]{6}\b', '', prompt)
    for pattern in TEXT_INSTRUCTION_PATTERNS:
        prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE)
    prompt = re.sub(r'\s{2,}', ' ', prompt)
    return prompt.strip().rstrip('.,')

def find_file(directory: Path, item_id: int, prefix: str) -> Path | None:
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = directory / f"item_{item_id}_{prefix}{ext}"
        if p.exists(): return p
    return None

def upload_to_fal(path: Path) -> str | None:
    try:
        url = fal_client.upload_file(str(path))
        return url
    except Exception:
        return None

def download_image(url: str, local_path: Path):
    with httpx.Client(timeout=60) as client:
        r = client.get(url, follow_redirects=True)
        r.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(r.content)

def image_to_base64(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64_data}"

def generate_image_for_item(item: dict, brand_context: dict) -> dict:
    content = item.get("content", {})
    image_prompt = content.get("image_prompt", "")
    text_on_image = content.get("text_on_image", "").strip()
    ideogram_style = content.get("ideogram_style", "DESIGN")
    layout_type = content.get("layout_type", "overlay") # Claude'un seçtiği şablon
    item_id = item.get("id")

    visuals = brand_context.get("visual_identity", {})
    corporate_colors = visuals.get("corporate_colors", [])
    background_colors = visuals.get("background_colors", [])
    
    color_injection = f" Integrates corporate colors: {', '.join(corporate_colors)}." if corporate_colors else ""
    bg_injection = f" Uses {', '.join(background_colors)} for background environment." if background_colors else ""

    # Logo Base64
    logo_b64 = ""
    logo_url = visuals.get("logo_url", "")
    if logo_url and logo_url.startswith("/assets/"):
        local_logo_path = BASE_DIR / logo_url.lstrip("/")
        if local_logo_path.exists():
            logo_b64 = image_to_base64(local_logo_path)
    elif logo_url.startswith("http"):
        logo_b64 = logo_url

    # Brand Element (Pie şekli vb.) Base64 YENİ EKLENDİ
    element_b64 = ""
    brand_element_url = visuals.get("brand_element_url", "")
    if brand_element_url and brand_element_url.startswith("/assets/"):
        local_elem_path = BASE_DIR / brand_element_url.lstrip("/")
        if local_elem_path.exists():
            element_b64 = image_to_base64(local_elem_path)
    elif brand_element_url.startswith("http"):
        element_b64 = brand_element_url

    if not image_prompt:
        raise ValueError(f"Item {item_id} has no image_prompt")

    base_prompt = clean_prompt(image_prompt)

    # DÜZELTME BURADA: Uzaylı telefonları ve şeffaf ekranları engelliyoruz
    if ideogram_style == "REALISTIC":
        style_suffix = "PHOTOREALISTIC photography. Corporate and professional. If showing devices or tablets, the screens should show abstract blurred modern UI graphs. NO transparent glass phones."
        negative_prompt = "text, words, letters, numbers, typography, watermark, logo, transparent glass phone, wireframe phone, sci-fi, blurry, low quality, distorted, actual UI text, labels"
    else:
        style_suffix = "Clean modern corporate graphic design composition. Abstract vector elements."
        negative_prompt = "text, words, letters, numbers, typography, font, label, caption, watermark, logo, transparent phone, wireframe phone, low quality"

    element_path = find_file(ELEMENTS_DIR, item_id, "element")
    style_path = find_file(REFERENCES_DIR, item_id, "style")

    element_url = upload_to_fal(element_path) if element_path else None
    style_url = upload_to_fal(style_path) if style_path else None

    filename = f"item_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    local_path = GENERATED_DIR / filename

    final_prompt = f"{base_prompt}.{color_injection}{bg_injection} {style_suffix} ABSOLUTELY NO ACTUAL TEXT OR LETTERS. USE WIREFRAME SKELETON LINES FOR UI ELEMENTS."
    print(f"  Prompt: {final_prompt[:180]}...")

    gen_arguments = {
        "prompt": final_prompt,
        "image_size": "square_hd",
        "style": ideogram_style,
        "rendering_speed": "TURBO",
        "magic_prompt_option": "AUTO",
        "negative_prompt": negative_prompt,
    }

    image_refs = []
    if style_url: image_refs.append({"image_url": style_url})
    if element_url: image_refs.append({"image_url": element_url})
    if image_refs:
        gen_arguments["image_references"] = image_refs
        gen_arguments["image_reference_strength"] = 0.50 

    result = fal_client.run("fal-ai/ideogram/v3", arguments=gen_arguments)

    image_url_remote = result["images"][0]["url"]
    download_image(image_url_remote, local_path)

    if text_on_image:
        bg_b64 = image_to_base64(local_path)
        # HTML Motoruna Logo, Element ve Şablon türünü yolluyoruz
        html_content = generate_brand_html(bg_b64, text_on_image, brand_context, logo_b64, element_b64, layout_type)
        asyncio.run(render_html_to_image(html_content, str(local_path)))

    item["image_url"] = f"/assets/generated/{filename}"
    item["image_local_path"] = str(local_path)
    item["image_generated_at"] = datetime.now().isoformat()
    item["image_style_ref_used"] = style_url is not None
    item["image_element_used"] = element_url is not None
    item["image_text_overlay"] = text_on_image or None
    item["layout_type"] = layout_type
    item["status"] = "image_generated"

    return item