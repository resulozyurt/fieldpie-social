import json
import anthropic
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.config import ANTHROPIC_API_KEY
from backend.app.modules.brand_module import load_brand_context, build_brand_system_prompt


def generate_content_calendar(month: int = None, year: int = None) -> dict:
    """
    Generate a monthly content calendar using Claude API.
    Returns a structured calendar with 12-16 content items.
    """
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year

    month_name = datetime(year, month, 1).strftime("%B %Y")

    context = load_brand_context()
    system_prompt = build_brand_system_prompt(context)

    user_prompt = f"""Generate a social media content calendar for {month_name} for FieldPie.

Create exactly 14 content items spread across LinkedIn and Instagram (3-4 posts per week).
Mix the content pillars: product features, industry insights, customer success, efficiency tips, company culture.

For each content item, return a JSON object with these exact fields:
- id: sequential number (1-14)
- date: specific date in {month_name} formatted as YYYY-MM-DD (spread evenly, skip weekends)
- platform: "LinkedIn" or "Instagram"
- content_pillar: one of the 5 content pillars
- format: "Educational", "Product Feature", "Success Story", "Tip", "Engagement", or "Behind the Scenes"
- topic: specific topic title (max 10 words)
- hook: attention-grabbing opening line for the post (max 15 words)
- notes: brief production notes for the content creator (max 20 words)
- status: always "pending"

Return ONLY a valid JSON object in this exact structure, no other text:
{{
  "month": "{month_name}",
  "generated_at": "ISO datetime",
  "total_items": 14,
  "items": [ ... array of 14 content items ... ]
}}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"Generating content calendar for {month_name}...")
    print("Calling Claude API...")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    response_text = message.content[0].text.strip()

    # Clean up response if it has markdown code blocks
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    calendar_data = json.loads(response_text)
    calendar_data["generated_at"] = datetime.now().isoformat()

    return calendar_data


def save_calendar(calendar_data: dict, output_dir: str = None) -> str:
    """Save the calendar to a JSON file and return the file path."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    month_slug = calendar_data["month"].replace(" ", "_").lower()
    filename = f"calendar_{month_slug}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(calendar_data, f, indent=2, ensure_ascii=False)

    return str(filepath)


def print_calendar_summary(calendar_data: dict):
    """Print a readable summary of the generated calendar."""
    print(f"\n{'='*60}")
    print(f"Content Calendar: {calendar_data['month']}")
    print(f"Total items: {calendar_data['total_items']}")
    print(f"{'='*60}")

    for item in calendar_data["items"]:
        platform_icon = "💼" if item["platform"] == "LinkedIn" else "📷"
        print(f"\n[{item['id']:02d}] {item['date']} {platform_icon} {item['platform']}")
        print(f"     Pillar : {item['content_pillar']}")
        print(f"     Format : {item['format']}")
        print(f"     Topic  : {item['topic']}")
        print(f"     Hook   : {item['hook']}")
        print(f"     Notes  : {item['notes']}")
        print(f"     Status : {item['status']}")

    print(f"\n{'='*60}")

    linkedin_count = sum(1 for i in calendar_data["items"] if i["platform"] == "LinkedIn")
    instagram_count = sum(1 for i in calendar_data["items"] if i["platform"] == "Instagram")
    print(f"LinkedIn: {linkedin_count} posts | Instagram: {instagram_count} posts")

    pillars = {}
    for item in calendar_data["items"]:
        p = item["content_pillar"]
        pillars[p] = pillars.get(p, 0) + 1
    print("\nContent pillar distribution:")
    for pillar, count in sorted(pillars.items()):
        print(f"  {pillar}: {count}")


if __name__ == "__main__":
    calendar = generate_content_calendar()
    print_calendar_summary(calendar)

    filepath = save_calendar(calendar)
    print(f"\nCalendar saved to: {filepath}")