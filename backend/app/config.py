import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file in development — Railway sets env vars directly
load_dotenv(Path(__file__).parent.parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY is not set. Add it to .env or Railway environment variables.")

if not FAL_KEY:
    raise ValueError("FAL_KEY is not set. Add it to .env or Railway environment variables.")
