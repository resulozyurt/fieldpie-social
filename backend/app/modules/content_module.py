import json
import re
import anthropic
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.config import ANTHROPIC_API_KEY

def generate_content_for_item(calendar_item: dict, brand_context: dict) -> dict:
    brand_details = brand_context.get("brand_details", {})
    brand_name = brand_details.get("name", "The Brand")
    description = brand_details.get("description", "A generic brand.")
    language = brand_details.get("language", "English")
    target_audience = brand_details.get("target_audience", "Global Professionals")

    visuals = brand_context.get("visual_identity", {})
    corporate_colors = visuals.get("corporate_colors", [])
    color_str = ", ".join(corporate_colors) if corporate_colors else "#005f56"
    font = visuals.get("typography", {}).get("primary", "sans-serif")

    system_prompt = f"You are an award-winning Copywriter and Art Director working for the brand '{brand_name}'."

    platform = calendar_item["platform"]
    topic = calendar_item["topic"]
    hook = calendar_item["hook"]
    format_type = calendar_item["format"]
    notes = calendar_item.get("notes", "")

    user_prompt = f"""Task: Prepare a complete, premium content package for the following social media post.
    Platform: {platform} | Format: {format_type} | Topic: {topic}
    Hook: {hook} | Strategy Note: {notes}
    
    BRAND CONTEXT:
    Brand Name: {brand_name}
    What they do: {description}
    Target Audience: {target_audience}
    Corporate Colors: {color_str}
    Output Language: {language}

    COPYWRITING RULES (Caption):
    - Language: MUST be written exactly in {language}.
    - Avoid corporate jargon. Write as if you are conversing with real humans.
    - Use PAS (Problem-Agitate-Solution) or AIDA copywriting frameworks.
    - Make the text highly readable using lists, arrows (→), or emojis.

    ART DIRECTION RULES (Image Prompt for Ideogram V3):
    - Language: The 'image_prompt' MUST ALWAYS be written in ENGLISH.
    - CREATIVITY & VARIETY: DO NOT just describe boring UI mockups or flat dashboards every time. Think outside the box! Use conceptual metaphors, abstract 3D layouts, dynamic office photography, cinematic angles, or surreal minimalist compositions.
    - ZERO TEXT: The image MUST NOT contain any words, letters, UI labels, text overlays, or numbers. I repeat: DO NOT ASK FOR ANY TEXT TO BE WRITTEN.
    - COLORS: Subtly weave the brand colors ({color_str}) into the lighting, props, or background environment.
    - IF REALISTIC: Ban plastic, doll-like AI appearances. Use terms like: "Shot on 35mm lens, cinematic lighting, candid photography, natural imperfections".
    - IF DESIGN: Apply rules like: "Minimalist, high contrast, editorial layout, utilizing negative space".

    The response MUST be ONLY the following JSON structure. No markdown formatting:
    {{
      "caption": "Perfectly written caption in {language}...",
      "image_prompt": "Ultra-detailed, creative, text-free English prompt for Ideogram V3...",
      "ideogram_style": "REALISTIC or DESIGN",
      "text_on_image": "A highly engaging, clickbaity, or curiosity-inducing 3-6 word HOOK (in {language}). MUST make the user stop scrolling! Examples: 'Stop doing this...', 'The ugly truth about...', '3 ways to scale...'",
      "description": "2-sentence alt text for accessibility and SEO (in {language})."
    }}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    response_text = message.content[0].text.strip()
    
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(0)

    return json.loads(response_text)