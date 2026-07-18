"""Loads configuration and API keys from the project-root .env file.

The .env lives one level up (C:\\Projects\\gridam\\.env) and is shared with
the Android build tooling, so we read from there rather than duplicating keys.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ -> project root
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENCHARGEMAP_API_KEY = os.getenv("OPENCHARGEMAP_API_KEY", "")
OPENROUTESERVICE_API_KEY = os.getenv(
    "OPENROUTESERVER_BASIC_API_KEY", os.getenv("OPENROUTESERVICE_API_KEY", "")
)
MAPTILER_API_KEY = os.getenv("MAPTILER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-safeguard-20b")
EM_API_KEY = os.getenv("EM_API_KEY", "")
EM_ZONE = os.getenv("EM_ZONE", "IN-SO")   # Electricity Maps zone (Kerala → Southern India)

# --- Demo region: Kochi, Kerala -------------------------------------------
KOCHI_LAT = 9.9312
KOCHI_LNG = 76.2673
DEFAULT_RADIUS_KM = 15

# --- Carbon model constants (tunable) -------------------------------------
EV_EFFICIENCY_KM_PER_KWH = 6.5      # typical EV range per kWh
PETROL_GCO2_PER_KM = 140.0          # equivalent petrol hatchback tailpipe
TREE_KG_CO2_PER_YEAR = 21.0         # ~1 mature tree absorbs ~21 kg CO2/yr

# DB location; override with GRIDAM_DB_PATH (e.g. on network/mounted drives
# where SQLite file locking misbehaves).
DB_PATH = Path(os.getenv("GRIDAM_DB_PATH", str(ROOT / "backend" / "gridam.db")))
