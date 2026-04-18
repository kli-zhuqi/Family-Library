from app.services.recommendation import recommend_student_types


def test_recommendation_stem():
    record = {"title": "Physics Workbook", "ocr_text": "Science physics engineering exam practice"}
    result = recommend_student_types(record)
    assert "stem_student" in result["recommended_student_types"]


def test_recommendation_default():
    result = recommend_student_types({"title": "Family Stories", "ocr_text": ""})
    assert result["recommended_student_types"]
