from .crops import CROPS, Crop


def make_recommendation(crop_name: str, temperature_c: float, precipitation_mm: float) -> dict:
    """Give a transparent, rule-based suggestion using today's forecast."""
    if crop_name not in CROPS:
        raise ValueError("Choose one of the supported crops.")
    if not isinstance(temperature_c, (int, float)) or not isinstance(precipitation_mm, (int, float)):
        raise ValueError("Temperature and precipitation must be numbers.")
    if temperature_c < -80 or temperature_c > 65 or precipitation_mm < 0:
        raise ValueError("Weather values are outside the expected range.")

    crop: Crop = CROPS[crop_name]
    warnings = []
    temperature_ok = crop.min_temperature <= temperature_c <= crop.max_temperature
    rainfall_ok = crop.low_rainfall_mm <= precipitation_mm <= crop.high_rainfall_mm

    if temperature_c < crop.min_temperature:
        warnings.append(f"Temperature is below the preferred range ({crop.min_temperature}-{crop.max_temperature} C).")
    elif temperature_c > crop.max_temperature:
        warnings.append(f"Temperature is above the preferred range ({crop.min_temperature}-{crop.max_temperature} C).")

    if precipitation_mm < crop.low_rainfall_mm:
        warnings.append("Rainfall forecast is low; irrigation may be needed.")
    elif precipitation_mm > crop.high_rainfall_mm:
        warnings.append("Heavy rainfall is forecast; check drainage and avoid waterlogged plots.")

    if temperature_ok and rainfall_ok:
        summary = f"Today's forecast looks broadly suitable for planting {crop_name.lower()}."
    else:
        summary = f"Conditions may be challenging for planting {crop_name.lower()} today."

    return {
        "summary": summary,
        "warnings": warnings,
        "temperature_suitable": temperature_ok,
        "rainfall_suitable": rainfall_ok,
        "water_need": crop.water_need,
        "disclaimer": "This uses today's forecast only, not seasonal rainfall or local soil conditions. Treat it as a basic guide.",
    }
