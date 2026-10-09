from dataclasses import dataclass


@dataclass(frozen=True)
class Crop:
    name: str
    min_temperature: float
    max_temperature: float
    water_need: str
    low_rainfall_mm: float
    high_rainfall_mm: float


CROPS = {
    "Maize": Crop("Maize", 18, 30, "Moderate", 5, 80),
    "Rice": Crop("Rice", 20, 32, "High", 10, 100),
    "Tomato": Crop("Tomato", 18, 27, "Moderate", 5, 50),
    "Cassava": Crop("Cassava", 20, 30, "Low", 2, 80),
}
