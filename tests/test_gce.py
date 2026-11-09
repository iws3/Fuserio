import json

import pytest

from localchat.gce import (
    LEARNING_MODES,
    STREAMS,
    SUBJECTS,
    build_tutor_system_prompt,
    load_progress,
    save_progress,
    suggested_topic_areas,
)


def test_subject_data_covers_each_requested_level_and_stream():
    assert tuple(SUBJECTS) == ("Ordinary Level", "Advanced Level")
    assert all(tuple(SUBJECTS[level]) == STREAMS for level in SUBJECTS)
    assert SUBJECTS["Ordinary Level"]["Sciences"] == [
        "Mathematics",
        "Additional Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "Human Biology",
        "Computer Science",
        "ICT",
        "Agricultural Science",
        "Food and Nutrition",
        "Physical Education",
    ]
    assert SUBJECTS["Advanced Level"]["Commercial"] == [
        "Economics",
        "Accounting",
        "Management in Living",
    ]


def test_tutor_prompt_is_level_and_subject_specific():
    ordinary_prompt = build_tutor_system_prompt("Ordinary Level", "Sciences", "Physics")
    advanced_prompt = build_tutor_system_prompt(
        "Advanced Level", "Sciences", "Pure Mathematics with Mechanics"
    )

    assert "Cameroon GCE Board" in ordinary_prompt
    assert "Ordinary Level" in ordinary_prompt
    assert "Physics" in ordinary_prompt
    assert "simple, clear, step-by-step" in ordinary_prompt
    assert "formula, substitution, intermediate step, unit" in ordinary_prompt
    assert "Cameroonian examples" in ordinary_prompt
    assert "Suggested study areas, not a verified or exhaustive official syllabus" in ordinary_prompt
    assert "deeper analysis suitable for A Level" in advanced_prompt
    assert "Never claim an invented question is an official past-paper question" in advanced_prompt


def test_topic_suggestions_are_subject_relevant_and_validated():
    topics = suggested_topic_areas("Ordinary Level", "Commercial", "Accounting")
    assert topics[0] == "Source documents and books of original entry"
    with pytest.raises(ValueError):
        suggested_topic_areas("Ordinary Level", "Languages", "Physics")


def test_progress_round_trips_locally(tmp_path):
    path = tmp_path / "gce-progress.json"
    progress = {
        "selection": {"level": "Ordinary Level", "stream": "Sciences", "subject": "Physics"},
        "sessions": {"Ordinary Level|Sciences|Physics": {"messages": [{"role": "user", "content": "Forces"}]}} ,
    }

    save_progress(progress, str(path))

    assert load_progress(str(path)) == progress
    assert json.loads(path.read_text(encoding="utf-8")) == progress
    assert not path.with_suffix(".json.tmp").exists()


def test_invalid_progress_file_returns_empty_state(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("not json", encoding="utf-8")

    assert load_progress(str(path)) == {"selection": {}, "sessions": {}}


def test_all_learning_modes_are_available():
    assert LEARNING_MODES == ("Lesson", "Practice", "Past-paper quiz", "Ask a question")
