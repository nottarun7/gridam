import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

KOCHI = {"lat": 9.9312, "lng": 76.2673}
DB_PATH = Path(os.getenv("GRIDAM_DB_PATH", ROOT / "data" / "gridam.db"))
EM_ZONE = os.getenv("EM_ZONE", "IN-SO")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
CARBON_CACHE = {"source": "kerala-model", "carbon": None, "renewable": None, "forecast": []}


def map_style_url() -> str:
    key = os.getenv("MAPTILER_API_KEY")
    return f"https://api.maptiler.com/maps/streets-v2-dark/style.json?key={key}" if key else "https://demotiles.maplibre.org/style.json"
