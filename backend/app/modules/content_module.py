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
    background_colors = visuals.get("background_colors", [])
    
    color_str = ", ".join(corporate_colors) if corporate_colors else "#005f56"
    bg_color_str = ", ".join(background_colors) if background_colors else "minimalist tones"

    system_prompt = f"You are an award-winning Copywriter and Art Director working for the brand '{brand_name}'."

    platform = calendar_item["platform"]
    topic = calendar_item["topic"]
    hook = calendar_item["hook"]
    format_type = calendar_item["format"]
    notes = calendar_item.get("notes", "")

    user_prompt = f"""Task: Prepare a complete, premium content package for the following social media post.
    Platform: {platform} | Format: {format_type} | Topic: {topic}
    
    BRAND CONTEXT:
    Brand Name: {brand_name}
    What they do: {description}
    Target Audience: {target_audience}
    Corporate Colors: {color_str}
    Output Language: {language}

    COPYWRITING RULES:
    - Language: MUST be written exactly in {language}.
    - Avoid corporate jargon. Write as if you are conversing with real humans.

    ART DIRECTION & LAYOUT RULES:
    - Language: The 'image_prompt' MUST ALWAYS be written in ENGLISH.
    - SKELETON UI: If your image features a dashboard or app, instruct the AI to use "abstract wireframe blocks, skeleton UI lines instead of text". BAN all actual letters.
    - LAYOUT SELECTION: You must choose the best visual layout for this post from these 3 options:
      1. 'overlay': Full cinematic image with a dark gradient at the bottom and text over it. Best for photography or strong emotional visuals.
      2. 'split': Top half is image, bottom half is a solid brand-colored block with text. Best for UI mockups, clear features, or data-driven posts.
      3. 'card': Blurred background image with a centered frosted-glass card containing the text. Best for quotes, statistics, or minimalist typography.

    The response MUST be ONLY the following JSON structure. No markdown formatting:
    {{
      "caption": "Perfectly written caption in {language}...",
      "image_prompt": "Ultra-detailed, creative, text-free English prompt for Ideogram V3 enforcing skeleton UI...",
      "ideogram_style": "REALISTIC or DESIGN",
      "layout_type": "overlay OR split OR card",
      "text_on_image": "A highly engaging, clickbaity 3-6 word HOOK (in {language}). Examples: 'Stop doing this...'",
      "description": "2-sentence alt text for accessibility (in {language})."
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