import json
from datetime import date
from pathlib import Path
from uuid import uuid4


DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "activities.json"
ALLOWED_ACTIVITIES = {"Planting", "Irrigation", "Weeding", "Fertilizing", "Harvesting"}
ALLOWED_CROPS = {"Maize", "Rice", "Tomato", "Cassava"}


def load_activities(path: str | Path = DEFAULT_DATA_PATH) -> list[dict]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("The activity file could not be read. Check its JSON format and permissions.") from error
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise ValueError("The activity file has an invalid format.")
    return data


def add_activity(
    activity: str,
    crop: str,
    activity_date: date,
    notes: str = "",
    path: str | Path = DEFAULT_DATA_PATH,
) -> dict:
    if activity not in ALLOWED_ACTIVITIES:
        raise ValueError("Choose a supported farm activity.")
    if crop not in ALLOWED_CROPS:
        raise ValueError("Choose a supported crop.")
    if not isinstance(activity_date, date):
        raise ValueError("Enter a valid activity date.")
    if len(notes.strip()) > 500:
        raise ValueError("Notes must be 500 characters or fewer.")

    records = load_activities(path)
    record = {
        "id": uuid4().hex,
        "activity": activity,
        "crop": crop,
        "date": activity_date.isoformat(),
        "notes": notes.strip(),
    }
    records.append(record)
    file_path = Path(path)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as error:
        raise ValueError("The activity could not be saved. Check the data folder permissions.") from error
    return record


def delete_activity(record_id: str, path: str | Path = DEFAULT_DATA_PATH) -> bool:
    records = load_activities(path)
    remaining = [record for record in records if record.get("id") != record_id]
    if len(remaining) == len(records):
        return False
    file_path = Path(path)
    try:
        file_path.write_text(json.dumps(remaining, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as error:
        raise ValueError("The activity could not be deleted. Check the data folder permissions.") from error
    return True
