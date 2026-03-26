import json
import anthropic
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.config import ANTHROPIC_API_KEY
from backend.app.modules.brand_module import load_brand_context, build_brand_system_prompt


def generate_content_for_item(calendar_item: dict, brand_context: dict) -> dict:
    system_prompt = build_brand_system_prompt(brand_context)
    platform = calendar_item["platform"]
    topic = calendar_item["topic"]
    hook = calendar_item["hook"]
    pillar = calendar_item["content_pillar"]
    format_type = calendar_item["format"]
    notes = calendar_item["notes"]

    user_prompt = f"""Generate a complete content package for this social media post:

Platform: {platform}
Content Pillar: {pillar}
Format: {format_type}
Topic: {topic}
Hook: {hook}
Production Notes: {notes}

Return ONLY a valid JSON object with these exact fields, no other text:

{{
  "caption": "Full post caption optimized for {platform}. {'Include line breaks, use → or bullet points for lists, end with 3-5 relevant hashtags. Max 1300 chars.' if platform == 'LinkedIn' else 'Punchy, visual-first, end with 5-8 hashtags. Max 300 chars.'}",

  "image_prompt": "A detailed Ideogram V3 prompt for a complete, ready-to-post social media graphic. The prompt must describe a FULL COMPOSITION including visual scene AND text overlay together as one image. Rules for the prompt you will write:

VISUAL SCENE RULES (choose the right one for this content):
- If topic involves people/teams/field work: Describe a photorealistic European professional aged 35-50, wearing casual shirt or blouse (NO suit, NO tie). Pose: either looking directly at camera with natural confident smile, OR looking down at tablet with focused expression — never gazing randomly to the side. Tablet: person holds or uses tablet naturally, screen does NOT need to be visible or legible. Setting must match topic: merchandising=retail store aisle, home service=outdoors near service vehicle, inspection=construction site or facility, office/software=modern bright office. Hyperrealistic photographic quality, real skin texture, natural light, sharp focus. Shot like a professional brand photography campaign.
- If topic involves data/statistics/ROI: Bold graphic design layout. Clean geometric shapes, strong color contrast. Teal (#019587) as primary color with white and dark accents. No people needed.
- If topic involves tips/steps/lists: Clean infographic design. Numbered layout, icons, clear visual hierarchy. White or light background with teal accents.
- If topic is engagement/question: Bold typographic design. Strong contrast, dynamic layout, one dominant visual element.

TEXT OVERLAY RULES (always include):
- Include the exact short headline text as a text overlay IN QUOTES in the prompt
- Maximum 6-8 words for headline, bold heavy sans-serif
- For photo posts: choose ONE creative text placement — floating white text top-left with subtle dark shadow, OR bold text on a solid rounded rectangle (not full-width gradient bar), OR large oversized text partially behind the subject for depth
- For graphic posts: centered dominant text, geometric accent shapes, clean whitespace
- AVOID: full-width gradient bars at the bottom, generic dark overlay covering half the image
- Think: how would a top creative agency place this text to feel fresh and editorial?

STYLE DECISION: Choose REALISTIC if the scene involves people, field workers, professionals, teams, physical locations, compliance, inspection, safety, retail or outdoor work. Choose DESIGN if the composition is purely graphic, data visualization, infographic, abstract, icon-based or typographic with no people needed.
BRAND COLORS: teal primary, white text, orange-red accent
NO generic logos, NO specific company names, NO hex codes written as text.
Max 400 chars total.",

  "ideogram_style": "REALISTIC or DESIGN — choose based on the image_prompt content you just wrote. REALISTIC if any people or real-world scene. DESIGN if purely graphic/infographic.",

  "text_on_image": "The exact short headline (max 8 words) that will appear in the image",

  "description": "SEO-friendly alt text. 2-3 sentences, includes main keywords naturally. Max 200 chars."
}}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    response_text = message.content[0].text.strip()

    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    return json.loads(response_text)


def generate_all_content(calendar_path: str = None) -> dict:
    if calendar_path is None:
        data_dir = Path(__file__).parent.parent / "data"
        now = datetime.now()
        month_slug = now.strftime("%B_%Y").lower()
        calendar_path = data_dir / f"calendar_{month_slug}.json"

    calendar_path = Path(calendar_path)
    if not calendar_path.exists():
        raise FileNotFoundError(f"Calendar file not found: {calendar_path}")

    with open(calendar_path, "r", encoding="utf-8") as f:
        calendar_data = json.load(f)

    brand_context = load_brand_context()
    total = len(calendar_data["items"])

    print(f"\nGenerating content for {total} items in {calendar_data['month']}...")

    for i, item in enumerate(calendar_data["items"], 1):
        if item.get("status") == "content_generated":
            print(f"[{i:02d}/{total}] Skipping: {item['topic'][:50]}")
            continue

        print(f"[{i:02d}/{total}] Generating: {item['topic'][:50]}...")

        try:
            content = generate_content_for_item(item, brand_context)
            item["content"] = content
            item["status"] = "content_generated"
            item["content_generated_at"] = datetime.now().isoformat()
            print(f"       ✓ {item['platform']} | {item['format']} | {content.get('ideogram_style', 'DESIGN')}")
        except Exception as e:
            print(f"       ✗ Error: {e}")
            item["status"] = "error"
            item["error"] = str(e)

        with open(calendar_path, "w", encoding="utf-8") as f:
            json.dump(calendar_data, f, indent=2, ensure_ascii=False)

    success_count = sum(1 for i in calendar_data["items"] if i.get("status") == "content_generated")
    print(f"\n✓ Done: {success_count}/{total}")
    return calendar_data


def print_content_preview(calendar_data: dict, item_id: int = 1):
    item = next((i for i in calendar_data["items"] if i["id"] == item_id), None)
    if not item:
        print(f"Item {item_id} not found")
        return
    content = item.get("content", {})
    print(f"\n{'='*60}")
    print(f"PREVIEW — Item #{item_id} | {item['platform']} | {item['format']}")
    print(f"Topic: {item['topic']}")
    print(f"\n--- CAPTION ---\n{content.get('caption', 'N/A')}")
    print(f"\n--- TEXT ON IMAGE ---\n{content.get('text_on_image', 'N/A')}")
    print(f"\n--- IMAGE PROMPT ---\n{content.get('image_prompt', 'N/A')}")
    print(f"\n--- STYLE ---\n{content.get('ideogram_style', 'N/A')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    calendar_data = generate_all_content()
    print_content_preview(calendar_data, item_id=1)