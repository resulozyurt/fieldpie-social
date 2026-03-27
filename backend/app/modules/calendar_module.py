import json
import re
import anthropic
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.config import ANTHROPIC_API_KEY
from backend.app.modules.intel_module import get_competitor_intel

def generate_content_calendar(month: int, year: int, brand_context: dict) -> dict:
    month_name = datetime(year, month, 1).strftime("%B %Y")
    
    # Settings'den gelen yeni dinamik verileri alıyoruz
    brand_details = brand_context.get("brand_details", {})
    brand_name = brand_details.get("name", brand_context.get("brand", {}).get("name", "The Brand"))
    description = brand_details.get("description", "A generic brand.")
    target_audience = brand_details.get("target_audience", "Professionals")
    language = brand_details.get("language", "English")
    
    competitors = brand_context.get("social_media", {}).get("competitors", [])
    
    print(f"Rakip istihbaratı toplanıyor: {competitors} ...")
    competitor_intel = "No competitor data available."
    if competitors and len(competitors) > 0:
        try:
            competitor_intel = get_competitor_intel(competitors)
        except Exception as e:
            print(f"Scraping Hatası (Yakalandı): {e}")

    system_prompt = f"You are a master Social Media Strategist for the brand '{brand_name}'."

    user_prompt = f"""You are a top-tier Social Media Strategist. Create a 14-post content calendar for the month of {month_name} for the brand '{brand_name}'.
    
    BRAND CONTEXT:
    - What they do: {description}
    - Target Audience: {target_audience}
    - Output Language: {language}
    
    COMPETITOR INTELLIGENCE (Last 30 Days):
    {competitor_intel}
    
    RULES:
    - Analyze the Competitor Intelligence provided above. What are they focusing on? Find their gaps and weaknesses.
    - Build a content strategy that OUTSMARTS them. Do not copy them; be more innovative.
    - Language: Write the 'topic', 'hook', and 'notes' STRICTLY in {language}.
    - Strategy: Avoid boring corporate jargon. Find scroll-stopping topics.
    - Distribution: Distribute the content evenly across LinkedIn and Instagram.
    - Content Pillars: Use pillars like Industry Insights, Success Stories, Product Intelligence, Team/Culture.
    
    The response MUST be ONLY a valid JSON object in the exact structure below. Do not include any markdown or other text:
    {{
      "month": "{month_name}",
      "total_items": 14,
      "items": [
        {{
          "id": 1,
          "date": "YYYY-MM-DD",
          "platform": "LinkedIn or Instagram",
          "content_pillar": "Industry Insights etc.",
          "format": "Carousel, Single Image, Infographic, Story",
          "topic": "Striking and specific topic title (max 8 words)",
          "hook": "Scroll-stopping first sentence to grab attention (max 12 words)",
          "notes": "What is the psychological trigger of this post?",
          "status": "pending"
        }}
      ]
    }}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    response_text = message.content[0].text.strip()
    
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(0)

    calendar_data = json.loads(response_text)
    calendar_data["generated_at"] = datetime.now().isoformat()

    return calendar_data