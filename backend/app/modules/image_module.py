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

# Çift yazı çıkmasını engellemek için çok daha agresif filtre
TEXT_INSTRUCTION_PATTERNS = [
    r'text\s+(overlay|reads?|says?|that\s+reads?)[^.]*\.',
    r'(bold\s+)?(white|black|teal|dark)?\s*text\s+["\'][^"\']*["\']',
    r'headline\s+["\'][^"\']*["\']',
    r'(floating|oversized|large)\s+text[^.]*\.',
    r'pill.shaped\s+tag[^.]*\.',
    r'rounded\s+rectangle[^.]*text[^.]*\.',
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
        print(f"  ✓ Uploaded {path.name}")
        return url
    except Exception as e:
        print(f"  ⚠ Upload failed: {e}")
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
    item_id = item.get("id")

    # Marka Kurumsal Renklerini Çekiyoruz
    visuals = brand_context.get("visual_identity", {})
    corporate_colors = visuals.get("corporate_colors", [])
    color_injection = f" Integrates corporate colors: {', '.join(corporate_colors)}." if corporate_colors else ""

    if not image_prompt:
        raise ValueError(f"Item {item_id} has no image_prompt")

    base_prompt = clean_prompt(image_prompt)

    if ideogram_style == "REALISTIC":
        style_suffix = "PHOTOREALISTIC photography. Real camera photo quality. Sharp focus. NOT illustration, NOT cartoon."
        negative_prompt = "text, words, letters, numbers, typography, watermark, logo, illustration, cartoon, anime, drawing, painting, sketch, render, 3D, CGI, comic, digital art, flat design, vector, clip art, animated, stylized, blurry, low quality, distorted, ui, dashboard, labels"
    else:
        style_suffix = "Clean graphic design composition. Pure visual composition only."
        negative_prompt = "text, words, letters, numbers, typography, font, label, caption, watermark, logo, blurry, low quality, distorted, ui elements, labels"

    element_path = find_file(ELEMENTS_DIR, item_id, "element")
    style_path = find_file(REFERENCES_DIR, item_id, "style")

    element_url = upload_to_fal(element_path) if element_path else None
    style_url = upload_to_fal(style_path) if style_path else None

    print(f"\n→ Item {item_id} | Style: {ideogram_style} | Element: {'✓' if element_url else '✗'} | Style ref: {'✓' if style_url else '✗'}")

    filename = f"item_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    local_path = GENERATED_DIR / filename

    # Agresif "Yazı Yazma" uyarısı ve Marka Renkleri eklendi
    final_prompt = f"{base_prompt}.{color_injection} {style_suffix} ABSOLUTELY NO TEXT, NO LETTERS, NO NUMBERS, NO UI LABELS IN THE IMAGE."
    print(f"  Prompt: {final_prompt[:180]}...")

    # Yaratıcılığı artırmak için magic_prompt_option "AUTO" yapıldı
    gen_arguments = {
        "prompt": final_prompt,
        "image_size": "square_hd",
        "style": ideogram_style,
        "rendering_speed": "TURBO",
        "magic_prompt_option": "AUTO",
        "negative_prompt": negative_prompt,
    }

    # Style ve Element Referanslarının İkisi de API'ye gönderiliyor (Sorun 5 Çözümü)
    image_refs = []
    if style_url:
        image_refs.append({"image_url": style_url})
    if element_url:
        image_refs.append({"image_url": element_url})

    if image_refs:
        gen_arguments["image_references"] = image_refs
        # Fal API'si liste uzunluğuna göre kendi ayarlamasını yapar
        gen_arguments["image_reference_strength"] = 0.50 

    result = fal_client.run("fal-ai/ideogram/v3", arguments=gen_arguments)

    image_url_remote = result["images"][0]["url"]
    print(f"  ✓ Ideogram generated — downloading...")
    download_image(image_url_remote, local_path)

    if text_on_image:
        print(f"  Applying HTML/CSS render for text: '{text_on_image}'")
        bg_b64 = image_to_base64(local_path)
        html_content = generate_brand_html(bg_b64, text_on_image, brand_context)
        
        asyncio.run(render_html_to_image(html_content, str(local_path)))
        print(f"  ✓ Dynamic Canvas rendered successfully")
    else:
        print(f"  No text_on_image — skipping overlay")

    item["image_url"] = f"/assets/generated/{filename}"
    item["image_local_path"] = str(local_path)
    item["image_generated_at"] = datetime.now().isoformat()
    item["image_style_ref_used"] = style_url is not None
    item["image_element_used"] = element_url is not None
    item["image_text_overlay"] = text_on_image or None
    item["status"] = "image_generated"

    print(f"✓ Done: {filename}")
    return item