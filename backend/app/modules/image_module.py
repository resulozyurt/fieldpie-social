import fal_client
import os
import re
import httpx
from pathlib import Path
from datetime import datetime
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.config import FAL_KEY

os.environ["FAL_KEY"] = FAL_KEY

BASE_DIR = Path(__file__).parent.parent.parent.parent
GENERATED_DIR = BASE_DIR / "assets" / "generated"
REFERENCES_DIR = BASE_DIR / "assets" / "references"
ELEMENTS_DIR = BASE_DIR / "assets" / "elements"
FONTS_DIR = BASE_DIR / "assets" / "fonts"

GENERATED_DIR.mkdir(parents=True, exist_ok=True)
REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
ELEMENTS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)

COLOR_TEAL_DARK = (0, 62, 62)
SYSTEM_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SYSTEM_FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Phrases that indicate text instructions inside a prompt — strip them
TEXT_INSTRUCTION_PATTERNS = [
    r'text\s+(overlay|reads?|says?|that\s+reads?)[^.]*\.',
    r'(bold\s+)?(white|black|teal|dark)?\s*text\s+["\'][^"\']*["\']',
    r'headline\s+["\'][^"\']*["\']',
    r'(floating|oversized|large)\s+text[^.]*\.',
    r'pill.shaped\s+tag[^.]*\.',
    r'rounded\s+rectangle[^.]*text[^.]*\.',
    r'reads?\s+["\'][^"\']*["\']',
    r'(caption|label|title|tagline)\s+["\'][^"\']*["\']',
]


def clean_prompt(prompt: str) -> str:
    """Remove hex codes, extra whitespace, and text overlay instructions from prompt."""
    # Remove hex color codes
    prompt = re.sub(r'#[0-9A-Fa-f]{6}\b', '', prompt)
    # Remove text instruction phrases
    for pattern in TEXT_INSTRUCTION_PATTERNS:
        prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE)
    # Clean up whitespace
    prompt = re.sub(r'\s{2,}', ' ', prompt)
    return prompt.strip().rstrip('.,')


def get_font(weight: str = "bold", size: int = 48) -> ImageFont.FreeTypeFont:
    font_map = {
        "bold":      ["Montserrat-Bold.ttf"],
        "extrabold": ["Montserrat-ExtraBold.ttf", "Montserrat-Bold.ttf"],
        "semibold":  ["Montserrat-SemiBold.ttf", "Montserrat-Bold.ttf"],
        "medium":    ["Montserrat-Medium.ttf", "Montserrat-Regular.ttf"],
        "regular":   ["Montserrat-Regular.ttf"],
    }
    for fname in font_map.get(weight, ["Montserrat-Bold.ttf"]):
        path = FONTS_DIR / fname
        if path.exists():
            return ImageFont.truetype(str(path), size)
    fallback = SYSTEM_FONT_BOLD if weight in ("bold", "extrabold", "semibold") else SYSTEM_FONT_REGULAR
    try:
        return ImageFont.truetype(fallback, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def find_best_pill_position(img: Image.Image, pill_w: int, pill_h: int) -> tuple[int, int]:
    """
    Scan the image in a grid to find the corner zone with most available
    bright/empty space for the pill. Returns (x1, y1).
    Checks 4 candidate zones: bottom-left, bottom-right, top-left, top-right.
    Picks the one with highest average brightness (lightest = most empty).
    """
    W, H = img.size
    gray = img.convert("L")
    margin = int(W * 0.05)
    pad = int(W * 0.04)

    candidates = [
        (margin, H - pill_h - margin - pad),           # bottom-left
        (W - pill_w - margin, H - pill_h - margin - pad),  # bottom-right
        (margin, margin + pad),                         # top-left
        (W - pill_w - margin, margin + pad),            # top-right
    ]

    best_pos = candidates[0]
    best_brightness = -1

    for (cx, cy) in candidates:
        # Keep within bounds
        cx = max(margin, min(cx, W - pill_w - margin))
        cy = max(margin, min(cy, H - pill_h - margin))
        region = gray.crop((cx, cy, cx + pill_w, cy + pill_h))
        import numpy as np
        arr = list(region.getdata())
        avg = sum(arr) / len(arr) if arr else 0
        if avg > best_brightness:
            best_brightness = avg
            best_pos = (cx, cy)

    return best_pos


def add_text_overlay(image_path: str, text: str) -> str:
    """Add Montserrat Bold text pill onto image. Overwrites in place."""
    if not text or not text.strip():
        return image_path

    img = Image.open(image_path).convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    max_text_width = int(W * 0.70)
    font_size = max(28, int(H * 0.052))
    font = get_font("bold", font_size)

    lines = wrap_text(text.upper(), font, max_text_width, draw)
    line_height = int(font_size * 1.22)
    block_h = line_height * len(lines)
    block_w = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)

    pad_x = int(W * 0.042)
    pad_y = int(H * 0.028)
    accent_w = 7

    pill_w = accent_w + pad_x + block_w + pad_x
    pill_h = pad_y + block_h + pad_y

    # Cap pill width
    pill_w = min(pill_w, int(W * 0.88))

    # Find best position
    pill_x1, pill_y1 = find_best_pill_position(img.convert("RGB"), pill_w, pill_h)
    pill_x2 = pill_x1 + pill_w
    pill_y2 = pill_y1 + pill_h

    radius = int(pill_h * 0.38)

    # Shadow
    draw.rounded_rectangle(
        [pill_x1 + 4, pill_y1 + 4, pill_x2 + 4, pill_y2 + 4],
        radius=radius, fill=(0, 0, 0, 65)
    )
    # White pill
    draw.rounded_rectangle(
        [pill_x1, pill_y1, pill_x2, pill_y2],
        radius=radius, fill=(255, 255, 255, 248)
    )
    # Teal accent bar
    bar_x1 = pill_x1 + radius // 2
    bar_x2 = bar_x1 + accent_w
    draw.rounded_rectangle(
        [bar_x1, pill_y1 + pad_y // 2, bar_x2, pill_y2 - pad_y // 2],
        radius=accent_w // 2, fill=(*COLOR_TEAL_DARK, 255)
    )
    # Text lines
    text_y = pill_y1 + pad_y
    for line in lines:
        draw.text((bar_x2 + pad_x, text_y), line, font=font, fill=(*COLOR_TEAL_DARK, 255))
        text_y += line_height

    Image.alpha_composite(img, overlay).convert("RGB").save(image_path, "PNG", quality=95)
    return image_path


def find_file(directory: Path, item_id: int, prefix: str) -> Path | None:
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = directory / f"item_{item_id}_{prefix}{ext}"
        if p.exists():
            return p
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


def generate_image_for_item(item: dict) -> dict:
    """
    Two-path generation:

    PATH A — Design Element exists:
        Use fal-ai/ideogram/v3/edit (image editing mode).
        The element image is the base canvas. Ideogram builds the design around it.
        This guarantees the element appears in the output.

    PATH B — Style reference only (or no references):
        Use fal-ai/ideogram/v3 standard generation.
        Style reference guides visual mood at strength 0.55.
    """
    content = item.get("content", {})
    image_prompt = content.get("image_prompt", "")
    text_on_image = content.get("text_on_image", "").strip()
    ideogram_style = content.get("ideogram_style", "DESIGN")
    item_id = item.get("id")

    if not image_prompt:
        raise ValueError(f"Item {item_id} has no image_prompt")

    # Clean prompt — remove text overlay instructions, hex codes
    base_prompt = clean_prompt(image_prompt)

    # Build style-appropriate prompt suffix
    if ideogram_style == "REALISTIC":
        style_suffix = (
            "PHOTOREALISTIC photography. Real camera photo quality. "
            "Real human skin, natural lighting, sharp focus. "
            "NOT illustration, NOT cartoon, NOT CGI, NOT 3D render. "
            "NO TEXT OR WORDS anywhere in the image."
        )
        negative_prompt = (
            "text, words, letters, numbers, typography, watermark, logo, "
            "illustration, cartoon, anime, drawing, painting, sketch, render, 3D, CGI, "
            "comic, digital art, flat design, vector, clip art, animated, stylized, "
            "blurry, low quality, distorted, "
            "suit and tie, tuxedo, formal wear"
        )
    else:
        style_suffix = (
            "Clean graphic design composition. "
            "NO TEXT, no words, no letters, no numbers anywhere in the image. "
            "Pure visual composition only."
        )
        negative_prompt = (
            "text, words, letters, numbers, typography, font, label, caption, "
            "watermark, logo, blurry, low quality, distorted"
        )

    # Check references
    element_path = find_file(ELEMENTS_DIR, item_id, "element")
    style_path = find_file(REFERENCES_DIR, item_id, "style")

    element_url = upload_to_fal(element_path) if element_path else None
    style_url = upload_to_fal(style_path) if style_path else None

    print(f"\n→ Item {item_id} | Style: {ideogram_style} | Element: {'✓' if element_url else '✗'} | Style ref: {'✓' if style_url else '✗'}")

    filename = f"item_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    local_path = GENERATED_DIR / filename

    final_prompt = f"{base_prompt}. {style_suffix}"
    print(f"  Prompt: {final_prompt[:180]}...")

    gen_arguments = {
        "prompt": final_prompt,
        "image_size": "square_hd",
        "style": ideogram_style,
        "rendering_speed": "TURBO",
        "magic_prompt_option": "OFF",
        "negative_prompt": negative_prompt,
    }

    # Style reference only — low strength to preserve creativity
    if style_url:
        gen_arguments["image_references"] = [{"image_url": style_url}]
        gen_arguments["image_reference_strength"] = 0.50
        print(f"  Style reference: strength 0.50")

    result = fal_client.run("fal-ai/ideogram/v3", arguments=gen_arguments)

    # Download result
    image_url_remote = result["images"][0]["url"]
    print(f"  ✓ Ideogram generated — downloading...")
    download_image(image_url_remote, local_path)

    # Pillow text overlay
    if text_on_image:
        print(f"  Applying text overlay: '{text_on_image}'")
        add_text_overlay(str(local_path), text_on_image)
        print(f"  ✓ Text overlay applied")
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