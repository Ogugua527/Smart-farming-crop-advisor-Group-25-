import pytest

from farming_advisor.recommendations import make_recommendation


def test_suitable_conditions_have_no_warnings():
    result = make_recommendation("Maize", temperature_c=27, precipitation_mm=20)
    assert "suitable" in result["summary"]
    assert result["warnings"] == []


def test_hot_and_dry_conditions_warn():
    result = make_recommendation("Tomato", temperature_c=34, precipitation_mm=0)
    assert len(result["warnings"]) == 2
    assert "above" in result["warnings"][0]
    assert "irrigation" in result["warnings"][1]


def test_unsupported_crop_is_rejected():
    with pytest.raises(ValueError):
        make_recommendation("Wheat", temperature_c=25, precipitation_mm=15)
