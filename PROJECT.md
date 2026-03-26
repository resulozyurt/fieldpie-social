# FieldPie Social Media Automation — Project Documentation

## Overview
Automated social media content pipeline for FieldPie (B2B SaaS, field operations management).
Platforms: LinkedIn + Instagram | Language: English | Frequency: 3-4 posts/week

---

## Tech Stack
- **Backend:** Python 3.12 + FastAPI + Uvicorn
- **AI - Content:** Anthropic Claude API (claude-sonnet-4-6)
- **AI - Images:** fal.ai → Ideogram 3 (text+image posts) + Recraft V3 (photographic)
- **Frontend:** React (to be built)
- **Database:** SQLite (to be added)
- **Hosting:** Railway (production)

## Environment Variables (.env)
```
ANTHROPIC_API_KEY=sk-ant-...
FAL_KEY=fal-...
```

---

## Project Structure
```
social_media_tool/
├── .env
├── .gitignore
├── PROJECT.md
├── assets/
│   ├── fieldpie-logo 1.png   (color)
│   ├── fieldpie-logo 2.png   (dark)
│   └── fieldpie-logo 3.png   (white)
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── config.py
│       ├── data/
│       │   ├── brand_context.json
│       │   └── calendar_march_2026.json   ← generated + content inside
│       └── modules/
│           ├── __init__.py
│           ├── brand_module.py
│           ├── calendar_module.py
│           └── content_module.py
├── frontend/             (to be built)
└── venv/
```

---

## Completed Phases

### ✅ Phase 1 — Brand Learning Module
- `brand_context.json`: Full brand identity, tone, colors, audience, competitors
- `brand_module.py`: Loads context, builds Claude system prompt (2796 chars)
- Test: `python -m backend.app.modules.brand_module`
- Status: **WORKING**

### ✅ Phase 2 — Monthly Content Calendar Generator
- `calendar_module.py`: Calls Claude API with brand system prompt
- Output: 14 content items (7 LinkedIn + 7 Instagram), balanced across 5 content pillars
- Saves to: `backend/app/data/calendar_MONTH_YEAR.json`
- Test: `python -m backend.app.modules.calendar_module`
- Status: **WORKING**

### ✅ Phase 3 — Content Generator
- `content_module.py`: Generates full content package per calendar item
- Output per item:
  - `caption`: Platform-optimized post text with hashtags
  - `visual_brief`: Detailed visual direction (concept, composition, colors, typography)
  - `image_prompt`: Ready-to-use Ideogram 3 prompt with hex codes and layout
  - `description`: SEO-friendly alt text
  - `text_on_image`: Short headline for image overlay (max 8 words)
- Skips already-generated items (no duplicate API calls)
- All content saved into `calendar_march_2026.json` under each item's `content` field
- Test: `python -m backend.app.modules.content_module`
- Status: **WORKING**

---

## In Progress

### 🔲 Phase 4 — FastAPI Backend + Web Interface
- FastAPI backend serving calendar data as REST API
- React frontend with:
  - Monthly calendar view (all 14 items)
  - Per-item detail panel: caption, visual brief, image prompt
  - Status buttons: Approve / Edit / Reject / Regenerate
  - Image preview panel (after Phase 5)
- Run: `uvicorn backend.app.main:app --reload`

### 🔲 Phase 5 — Image Generation
- Module: `backend/app/modules/image_module.py`
- fal.ai → Ideogram 3 for text+image posts
- Triggered from UI after content approval
- Generated images saved to `assets/generated/`
- Image URL stored in calendar JSON

### 🔲 Phase 6 — Auto Publishing
- Module: `backend/app/modules/publisher_module.py`
- LinkedIn API
- Meta Graph API (Instagram)
- Scheduled publishing based on calendar dates

---

## Monthly Cost Estimate
| Item | Cost |
|---|---|
| Claude API (Sonnet) | ~$3–5 |
| fal.ai (Ideogram 3, 12-16 images) | ~$0.50–1 |
| Railway hosting | ~$5–7 |
| LinkedIn + Meta API | $0 |
| **Total** | **~$9–13/month** |

---

## How to Resume This Project
1. Open `social_media_tool` folder in VS Code
2. Activate venv: `venv\Scripts\activate`
3. Read this file to see where we left off
4. Paste this file into a new Claude conversation to continue

## Run Commands
```bash
# Activate venv (always first)
venv\Scripts\activate

# Test brand module
python -m backend.app.modules.brand_module

# Generate content calendar (Phase 2)
python -m backend.app.modules.calendar_module

# Generate content packages (Phase 3)
python -m backend.app.modules.content_module
```
