import json
import anthropic
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.config import ANTHROPIC_API_KEY
from backend.app.modules.brand_module import build_brand_system_prompt

def generate_content_for_item(calendar_item: dict, brand_context: dict) -> dict:
    system_prompt = build_brand_system_prompt(brand_context)
    
    brand_name = brand_context.get("brand", {}).get("name", "The Brand")
    tone = brand_context.get("brand", {}).get("tone_of_voice", "Professional and reliable")
    visuals = brand_context.get("visual_identity", {})
    primary_color = visuals.get("primary_color", "brand primary color")
    font = visuals.get("typography", {}).get("primary", "sans-serif")
    target_audience = brand_context.get("brand", {}).get("target_audience", "Global Professionals")

    platform = calendar_item["platform"]
    topic = calendar_item["topic"]
    hook = calendar_item["hook"]
    format_type = calendar_item["format"]
    notes = calendar_item.get("notes", "")

    user_prompt = f"""You are an award-winning Copywriter and Art Director working for the brand '{brand_name}'.
    Brand Tone of Voice: {tone}
    Corporate Color: {primary_color}, Font: {font}
    Target Audience: {target_audience}

    Task: Prepare a complete, premium content package for the following social media post.
    Platform: {platform} | Format: {format_type} | Topic: {topic}
    Hook: {hook} | Strategy Note: {notes}

    COPYWRITING RULES (Caption):
    - Language: MUST be written in the native language of the Target Audience (e.g., Turkish for Turkey, English for US).
    - Avoid corporate jargon. Write as if you are conversing with real humans.
    - Use PAS (Problem-Agitate-Solution) or AIDA copywriting frameworks.
    - Make the text highly readable using lists, arrows (→), or emojis.

    ART DIRECTION RULES (Image Prompt for Ideogram V3):
    - Language: The 'image_prompt' MUST ALWAYS be written in ENGLISH, regardless of the target audience language.
    - IF REALISTIC (contains humans): Ban plastic, doll-like AI appearances. Use terms like: "Shot on 35mm lens, cinematic lighting, real skin texture, candid photography, slight motion blur, natural imperfections". Subtly incorporate the {primary_color} color into small details (e.g., tie, coffee mug, background light).
    - IF DESIGN (graphic/infographic): Apply rules like: "Minimalist, flat design, high contrast, editorial layout, utilizing {primary_color} and negative space".
    - DO NOT include the headline or any specific text in the image_prompt. The text will be added later programmatically. Focus ONLY on the visual composition, lighting, style, and environment.

    The response MUST be ONLY the following JSON structure. No markdown formatting:
    {{
      "caption": "Perfectly written caption in the target audience's language...",
      "image_prompt": "Ultra-detailed, cinematic English prompt for Ideogram V3...",
      "ideogram_style": "REALISTIC or DESIGN",
      "text_on_image": "Short impactful text to appear on the image (in audience's language)",
      "description": "2-sentence alt text for accessibility and SEO (in audience's language)."
    }}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = "\n".join(response_text.split("\n")[1:-1])

    return json.loads(response_text)