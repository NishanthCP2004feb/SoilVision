from ml.src.preprocessing.split_dataset import grouped_split
from backend.app.schemas.domain import RecommendationInput
from backend.app.services.recommendations import CropProfile, recommend


def test_related_groups_never_cross_split() -> None:
    rows = [
        {"path": "a.jpg", "label": "A", "group_id": "g1"}, {"path": "b.jpg", "label": "A", "group_id": "g1"},
        {"path": "c.jpg", "label": "A", "group_id": "g2"}, {"path": "d.jpg", "label": "A", "group_id": "g3"},
        {"path": "e.jpg", "label": "B", "group_id": "g4"}, {"path": "f.jpg", "label": "B", "group_id": "g5"}, {"path": "g.jpg", "label": "B", "group_id": "g6"},
    ]
    result = grouped_split(rows, seed=7)
    assigned = {}
    for split, members in result.items():
        for row in members:
            assert assigned.setdefault(row["group_id"], split) == split


def test_recommendation_reports_limited_evidence() -> None:
    profile = CropProfile("Example", ("Black_Soil",), ("Kharif",), ("https://example.invalid/source",), {})
    result = recommend(RecommendationInput(soil_type="Black_Soil", season="Kharif"), [profile])[0]
    assert result["compatibility_score"] == 100
    assert "available verified measurements" in result["warning"]
