from __future__ import annotations

from collections import defaultdict

STUDENT_TYPES = [
    "early_reader",
    "visual_learner",
    "struggling_reader",
    "advanced_reader",
    "stem_student",
    "humanities_student",
    "language_learner",
    "exam_prep_student",
    "creative_student",
    "general_family_reading",
]

KEYWORDS = {
    "early_reader": ["phonics", "first words", "beginner", "learn to read", "abc"],
    "struggling_reader": ["remedial", "beginner", "easy", "practice reading"],
    "stem_student": ["science", "math", "coding", "engineering", "physics", "chemistry"],
    "humanities_student": ["history", "literature", "poetry", "philosophy", "essay"],
    "language_learner": ["vocabulary", "grammar", "writing", "english", "dictionary"],
    "exam_prep_student": ["exam", "test", "practice", "sat", "ielts", "toefl", "workbook"],
    "creative_student": ["drawing", "music", "story", "storytelling", "craft", "imagination", "art"],
}


def infer_subject_tags(record: dict) -> list[str]:
    text = f"{record.get('title', '')} {record.get('ocr_text', '')}".lower()
    tags = []
    for tag, words in {
        "stem": ["science", "math", "engineering", "technology"],
        "language": ["vocabulary", "grammar", "english"],
        "humanities": ["history", "literature", "poetry"],
        "creative": ["drawing", "music", "art"],
        "exam-prep": ["test", "exam", "practice"],
    }.items():
        if any(word in text for word in words):
            tags.append(tag)
    return tags or ["general"]


def infer_reading_level(record: dict) -> str:
    text = (record.get("ocr_text") or "").strip()
    words = len(text.split())
    title = (record.get("title") or "").lower()
    if any(word in title for word in ["phonics", "beginner", "first words"]):
        return "early"
    if words < 20:
        return "picture_book"
    if words < 80:
        return "intermediate"
    return "advanced"


def recommend_student_types(record: dict) -> dict:
    text = f"{record.get('title', '')} {record.get('ocr_text', '')}".lower()
    scores = defaultdict(float)

    for student_type, words in KEYWORDS.items():
        for word in words:
            if word in text:
                scores[student_type] += 1.5

    word_count = len((record.get("ocr_text") or "").split())
    if word_count < 25:
        scores["visual_learner"] += 1.2
        scores["early_reader"] += 0.8
    elif word_count > 120:
        scores["advanced_reader"] += 1.4

    if not scores:
        scores["general_family_reading"] = 1.0

    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top = [k for k, _ in sorted_scores[:3]]
    explanation = f"Matched to {', '.join(top)} based on detected keywords and text density."
    return {
        "recommended_student_types": top,
        "recommendation_scores": dict(sorted_scores),
        "recommendation_explanation": explanation,
    }


def generate_book_note_summary(record: dict) -> str:
    title = record.get("title") or "Unknown title"
    author = record.get("author") or "Unknown author"
    types = record.get("recommended_student_types") or []
    return f"{title} by {author}. Best for: {', '.join(types) if types else 'general family reading'}."
