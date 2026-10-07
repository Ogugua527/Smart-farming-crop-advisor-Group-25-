import json
from datetime import date

from farming_advisor.storage import add_activity, delete_activity, load_activities


def test_activity_round_trip_and_delete(tmp_path):
    path = tmp_path / "activities.json"
    record = add_activity("Planting", "Maize", date(2026, 10, 4), "North field", path)

    assert load_activities(path) == [record]
    assert json.loads(path.read_text(encoding="utf-8"))[0]["date"] == "2026-10-04"
    assert delete_activity(record["id"], path) is True
    assert load_activities(path) == []


def test_missing_activity_file_is_empty(tmp_path):
    assert load_activities(tmp_path / "missing.json") == []
