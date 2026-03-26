import json
import os
from pathlib import Path


def load_brand_context() -> dict:
    """Load brand context from JSON file."""
    data_dir = Path(__file__).parent.parent / "data"
    brand_file = data_dir / "brand_context.json"

    if not brand_file.exists():
        raise FileNotFoundError(f"brand_context.json not found at {brand_file}")

    with open(brand_file, "r", encoding="utf-8") as f:
        return json.load(f)


def build_brand_system_prompt(context: dict) -> str:
    """Build a system prompt from brand context for use in all Claude API calls."""
    brand = context["brand"]
    visual = context["visual_identity"]
    social = context["social_media"]

    prompt = f"""You are a senior social media content strategist for {brand["name"]}.

## About {brand["name"]}
{brand["description"]}

Tagline: "{brand["tagline"]}"

## Brand Voice & Tone
{brand["tone"]}

## Target Audience
{chr(10).join(f"- {a}" for a in brand["target_audience"])}

## Key Features
{chr(10).join(f"- {f}" for f in brand["key_features"])}

## Pain Points We Solve
{chr(10).join(f"- {p}" for p in brand["pain_points_solved"])}

## What Makes Us Different
{chr(10).join(f"- {d}" for d in brand["differentiators"])}

## Competitive Landscape
Global competitors: {", ".join(brand["competitors"]["global"])}
Local/regional competitors: {", ".join(brand["competitors"]["local"])}

## Visual Identity
Logo: {visual["logo_description"]}
Visual style: {visual["visual_style"]}

Primary colors:
- Deep Teal (PM500): {visual["primary_colors"]["PM500"]}
- Teal (PM300): {visual["primary_colors"]["PM300"]}
- Light Teal (PM100): {visual["primary_colors"]["PM100"]}

Secondary colors:
- Dark Gray (SC500): {visual["secondary_colors"]["SC500"]}
- Slate (SC300): {visual["secondary_colors"]["SC300"]}
- Light Slate (SC100): {visual["secondary_colors"]["SC100"]}

Accent colors: Red {visual["accent_colors"]["red"]}, Yellow {visual["accent_colors"]["yellow"]}, Green {visual["accent_colors"]["green"]}

## Social Media Strategy
Platforms: {", ".join(social["platforms"])}
LinkedIn focus: {social["linkedin_focus"]}
Instagram focus: {social["instagram_focus"]}
Posting frequency: {social["posting_frequency"]}
Language: {social["language"]}

## Content Pillars
{chr(10).join(f"- {p}" for p in social["content_pillars"])}

## Important Rules
- Always write in {social["language"]}
- Never use generic corporate speak or buzzwords
- Always focus on real operational value for field teams
- Keep LinkedIn content professional and insight-driven
- Keep Instagram content visually descriptive and engaging
- Never mention competitor names in content
- Always align with the teal and dark gray visual identity
"""
    return prompt


def get_brand_summary() -> str:
    """Return a short human-readable brand summary for logging and debugging."""
    context = load_brand_context()
    brand = context["brand"]
    return (
        f"Brand: {brand['name']} | "
        f"Tone: {brand['tone'][:50]}... | "
        f"Platforms: {', '.join(context['social_media']['platforms'])} | "
        f"Frequency: {context['social_media']['posting_frequency']}"
    )


if __name__ == "__main__":
    print("Loading brand context...")
    context = load_brand_context()
    print(f"Brand loaded: {context['brand']['name']}")
    print()
    print("Brand summary:")
    print(get_brand_summary())
    print()
    print("System prompt preview (first 500 chars):")
    prompt = build_brand_system_prompt(context)
    print(prompt[:500])
    print("...")
    print(f"\nTotal system prompt length: {len(prompt)} characters")