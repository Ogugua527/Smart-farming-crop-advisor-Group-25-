"""
crop.py  --  Role 4: Crop Knowledge & Crop Module
Group 25 | Smart Farming & Crop Planting Advisor

Responsibilities (from the proposal):
  1. Store crop-specific data for maize, cassava, tomato and rice.
  2. Provide crop selection + validation so supported crops are accepted consistently.
  3. Give structured crop data to the AI advisor (Role 2) and other modules.

Public API (what other team members import):
  get_supported_crops()            -> ["cassava", "maize", "rice", "tomato"]
  normalize_crop_name(text)        -> "maize"   (handles "Corn", " MAIZE ", "tomatoes")
  is_supported_crop(text)          -> bool
  validate_crop(text)              -> "maize"   or raises UnsupportedCropError
  get_crop(text)                   -> Crop object
  get_crop_data(text)              -> dict      (for Role 2 / Role 5 / JSON storage)
  get_crop_prompt_context(text)    -> str       (ready to paste into a Gemini prompt)
  check_weather_suitability(text, weather) -> dict (compares Role 1's weather to crop needs)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class UnsupportedCropError(ValueError):
    """Raised when the farmer enters a crop the system does not support."""


# --------------------------------------------------------------------------- #
# Crop data structure
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Crop:
    """Immutable record of the planting requirements for one crop."""

    name: str
    scientific_name: str
    category: str                         # cereal / root tuber / vegetable
    # Temperature (degrees C)
    temp_min_c: float                     # below this growth is poor
    temp_max_c: float                     # above this heat stress occurs
    temp_optimal_min_c: float
    temp_optimal_max_c: float
    # Rainfall (mm over the whole growing season)
    rainfall_min_mm: int
    rainfall_max_mm: int
    # Duration (days from planting to harvest)
    growth_days_min: int
    growth_days_max: int
    # Soil
    soil_ph_min: float
    soil_ph_max: float
    soil_types: tuple
    # Planting practice
    spacing_cm: str                       # "row x plant"
    planting_depth: str
    planting_method: str
    water_requirement: str                # low / medium / high / very high
    waterlogging_tolerance: str           # low / medium / high
    # Calendar (southern / northern Nigeria, months as text)
    planting_months_south: tuple
    planting_months_north: tuple
    # Risks and care
    common_pests: tuple = field(default_factory=tuple)
    common_diseases: tuple = field(default_factory=tuple)
    critical_stages: tuple = field(default_factory=tuple)
    notes: str = ""


# --------------------------------------------------------------------------- #
# Crop knowledge base  (approximate agronomic values -- verify with extension
# guides such as IITA / FAO if you want to cite sources in the report)
# --------------------------------------------------------------------------- #
CROPS: dict[str, Crop] = {
    "maize": Crop(
        name="maize",
        scientific_name="Zea mays",
        category="cereal",
        temp_min_c=10, temp_max_c=35,
        temp_optimal_min_c=18, temp_optimal_max_c=32,
        rainfall_min_mm=500, rainfall_max_mm=1200,
        growth_days_min=90, growth_days_max=120,
        soil_ph_min=5.5, soil_ph_max=7.0,
        soil_types=("loamy", "sandy loam", "well-drained"),
        spacing_cm="75 x 25",
        planting_depth="3-5 cm",
        planting_method="Direct seeding, 1-2 seeds per hole",
        water_requirement="medium",
        waterlogging_tolerance="low",
        planting_months_south=("March", "April", "August", "September"),
        planting_months_north=("May", "June", "July"),
        common_pests=("Fall armyworm", "Stem borers"),
        common_diseases=("Maize streak virus", "Rust", "Leaf blight"),
        critical_stages=("Germination", "Tasseling", "Silking"),
        notes="Needs adequate moisture at tasseling/silking; avoid waterlogged fields.",
    ),
    "cassava": Crop(
        name="cassava",
        scientific_name="Manihot esculenta",
        category="root tuber",
        temp_min_c=20, temp_max_c=35,
        temp_optimal_min_c=25, temp_optimal_max_c=29,
        rainfall_min_mm=1000, rainfall_max_mm=1500,
        growth_days_min=270, growth_days_max=365,
        soil_ph_min=5.5, soil_ph_max=6.5,
        soil_types=("sandy loam", "loamy", "well-drained"),
        spacing_cm="100 x 100",
        planting_depth="5-10 cm (stem cutting 20-25 cm long)",
        planting_method="Stem cuttings planted upright or slanted on ridges/mounds",
        water_requirement="low",
        waterlogging_tolerance="low",
        planting_months_south=("March", "April", "May", "June", "September", "October"),
        planting_months_north=("May", "June"),
        common_pests=("Cassava mealybug", "Green mite"),
        common_diseases=("Cassava mosaic disease", "Bacterial blight"),
        critical_stages=("Establishment (first 3 months)",),
        notes="Drought tolerant once established; use disease-free cuttings; root rots in waterlogged soil.",
    ),
    "tomato": Crop(
        name="tomato",
        scientific_name="Solanum lycopersicum",
        category="vegetable",
        temp_min_c=10, temp_max_c=35,
        temp_optimal_min_c=18, temp_optimal_max_c=27,
        rainfall_min_mm=400, rainfall_max_mm=800,
        growth_days_min=90, growth_days_max=140,
        soil_ph_min=6.0, soil_ph_max=6.8,
        soil_types=("loamy", "sandy loam", "well-drained"),
        spacing_cm="60 x 45",
        planting_depth="0.5-1 cm (nursery seed); transplant at 3-4 weeks",
        planting_method="Raise seedlings in a nursery, then transplant",
        water_requirement="high",
        waterlogging_tolerance="low",
        planting_months_south=("September", "October", "November", "February"),
        planting_months_north=("October", "November", "February"),
        common_pests=("Tuta absoluta", "Whitefly", "Fruit borer"),
        common_diseases=("Early blight", "Late blight", "Bacterial wilt", "Fusarium wilt"),
        critical_stages=("Transplanting", "Flowering", "Fruit set"),
        notes="Heavy rain promotes blight and fruit cracking; stake plants and mulch.",
    ),
    "rice": Crop(
        name="rice",
        scientific_name="Oryza sativa",
        category="cereal",
        temp_min_c=20, temp_max_c=35,
        temp_optimal_min_c=25, temp_optimal_max_c=32,
        rainfall_min_mm=1000, rainfall_max_mm=2000,
        growth_days_min=90, growth_days_max=150,
        soil_ph_min=5.5, soil_ph_max=7.0,
        soil_types=("clay", "clay loam", "poorly-drained (paddy)"),
        spacing_cm="20 x 20",
        planting_depth="2-3 cm (direct seeding) or transplant at 21-30 days",
        planting_method="Direct seeding or transplanting seedlings into puddled fields",
        water_requirement="very high",
        waterlogging_tolerance="high",
        planting_months_south=("March", "April", "May", "July", "August"),
        planting_months_north=("June", "July"),
        common_pests=("Stem borers", "African rice gall midge", "Birds"),
        common_diseases=("Rice blast", "Rice yellow mottle virus"),
        critical_stages=("Tillering", "Flowering", "Grain filling"),
        notes="Needs standing water for most of the season; drain before harvest.",
    ),
}

# Alternative names a farmer might type -> canonical crop key
ALIASES: dict[str, str] = {
    "corn": "maize", "maize": "maize", "zea mays": "maize",
    "cassava": "cassava", "manioc": "cassava", "yuca": "cassava", "garri": "cassava",
    "tomato": "tomato", "tomatoes": "tomato", "tomatos": "tomato",
    "rice": "rice", "paddy": "rice", "paddy rice": "rice",
}


# --------------------------------------------------------------------------- #
# Selection & validation
# --------------------------------------------------------------------------- #
def get_supported_crops() -> list[str]:
    """Sorted list of canonical crop names (use this to fill a Streamlit selectbox)."""
    return sorted(CROPS)


def normalize_crop_name(raw: Optional[str]) -> Optional[str]:
    """
    Turn raw user text into a canonical crop key, or None if not recognised.
    Handles case, extra spaces, punctuation, plurals and common aliases.
    """
    if not isinstance(raw, str):
        return None
    cleaned = re.sub(r"[^a-z\s]", "", raw.lower())      # drop digits/punctuation
    cleaned = re.sub(r"\s+", " ", cleaned).strip()      # collapse whitespace
    if not cleaned:
        return None
    if cleaned in ALIASES:
        return ALIASES[cleaned]
    if cleaned.endswith("s") and cleaned[:-1] in ALIASES:   # simple plural fallback
        return ALIASES[cleaned[:-1]]
    return None


def is_supported_crop(raw: Optional[str]) -> bool:
    return normalize_crop_name(raw) is not None


def validate_crop(raw: Optional[str]) -> str:
    """Return the canonical crop name or raise UnsupportedCropError with a friendly message."""
    crop = normalize_crop_name(raw)
    if crop is None:
        supported = ", ".join(c.capitalize() for c in get_supported_crops())
        shown = raw if isinstance(raw, str) and raw.strip() else "(empty)"
        raise UnsupportedCropError(
            f"Crop '{shown}' is not supported. Please choose one of: {supported}."
        )
    return crop


def get_crop(raw: str) -> Crop:
    """Validated lookup that returns the Crop object."""
    return CROPS[validate_crop(raw)]


# --------------------------------------------------------------------------- #
# Structured output for other modules
# --------------------------------------------------------------------------- #
def get_crop_data(raw: str) -> dict:
    """Plain dict of the crop's data -- JSON-serialisable (Role 5 can store it, Role 2 can use it)."""
    data = asdict(get_crop(raw))
    # tuples -> lists so json.dumps / json.loads round-trips identically
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in data.items()}


def get_crop_prompt_context(raw: str) -> str:
    """Compact text block Role 2 can drop straight into the Gemini prompt."""
    c = get_crop(raw)
    return (
        f"Crop: {c.name.capitalize()} ({c.scientific_name}), {c.category}\n"
        f"- Optimal temperature: {c.temp_optimal_min_c}-{c.temp_optimal_max_c} C "
        f"(tolerable {c.temp_min_c}-{c.temp_max_c} C)\n"
        f"- Seasonal rainfall need: {c.rainfall_min_mm}-{c.rainfall_max_mm} mm\n"
        f"- Growth duration: {c.growth_days_min}-{c.growth_days_max} days\n"
        f"- Soil: pH {c.soil_ph_min}-{c.soil_ph_max}, {', '.join(c.soil_types)}\n"
        f"- Spacing: {c.spacing_cm} cm; depth: {c.planting_depth}\n"
        f"- Method: {c.planting_method}\n"
        f"- Water requirement: {c.water_requirement}; waterlogging tolerance: {c.waterlogging_tolerance}\n"
        f"- Typical planting months (south): {', '.join(c.planting_months_south)}\n"
        f"- Typical planting months (north): {', '.join(c.planting_months_north)}\n"
        f"- Common pests: {', '.join(c.common_pests)}\n"
        f"- Common diseases: {', '.join(c.common_diseases)}\n"
        f"- Critical growth stages: {', '.join(c.critical_stages)}\n"
        f"- Notes: {c.notes}"
    )


def check_weather_suitability(raw: str, weather: dict) -> dict:
    """
    Compare Role 1's weather dict to the crop's needs.

    Expected (optional) keys in `weather` -- agree the exact names with Role 1/Role 3:
        "temperature_c"      current/average temperature
        "rainfall_mm"        forecast or recent rainfall total
        "soil_temperature_c" (optional, not used for scoring yet)

    Returns {"crop": str, "suitable": bool | None, "warnings": [str], "checks": {...}}
    Missing keys are skipped, never crash.
    """
    c = get_crop(raw)
    warnings: list[str] = []
    checks: dict[str, str] = {}

    temp = weather.get("temperature_c") if isinstance(weather, dict) else None
    if isinstance(temp, (int, float)):
        if temp < c.temp_min_c:
            checks["temperature"] = "too cold"
            warnings.append(f"Temperature {temp} C is below the minimum {c.temp_min_c} C for {c.name}.")
        elif temp > c.temp_max_c:
            checks["temperature"] = "too hot"
            warnings.append(f"Temperature {temp} C is above the maximum {c.temp_max_c} C for {c.name}.")
        elif c.temp_optimal_min_c <= temp <= c.temp_optimal_max_c:
            checks["temperature"] = "optimal"
        else:
            checks["temperature"] = "acceptable"

    rain = weather.get("rainfall_mm") if isinstance(weather, dict) else None
    if isinstance(rain, (int, float)):
        # Weather APIs return short-term totals, so only flag extremes against waterlogging risk.
        if rain > 100 and c.waterlogging_tolerance == "low":
            checks["rainfall"] = "heavy rain risk"
            warnings.append(f"Heavy rainfall ({rain} mm) may waterlog {c.name}; ensure good drainage.")
        elif rain < 1 and c.water_requirement in ("high", "very high"):
            checks["rainfall"] = "dry"
            warnings.append(f"Little rainfall expected; {c.name} has {c.water_requirement} water needs, plan irrigation.")
        else:
            checks["rainfall"] = "ok"

    suitable = None if not checks else not any(
        v in ("too cold", "too hot") for v in checks.values()
    )
    return {"crop": c.name, "suitable": suitable, "warnings": warnings, "checks": checks}


# --------------------------------------------------------------------------- #
# Quick manual demo:  python crop.py
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("Supported crops:", get_supported_crops())
    print(validate_crop("  Corn "))
    print(get_crop_prompt_context("cassava"))
    print(check_weather_suitability("tomato", {"temperature_c": 38, "rainfall_mm": 120}))
    try:
        validate_crop("yam")
    except UnsupportedCropError as err:
        print("Error:", err)