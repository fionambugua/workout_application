from datetime import date

import pytest
from marshmallow import ValidationError

from schemas import (
    exercise_detail_schema,
    exercise_schema,
    workout_detail_schema,
    workout_exercise_schema,
    workout_schema,
)


# ---------- Serialization ----------

def test_workout_detail_includes_exercises_and_metrics(sample):
    data = workout_detail_schema.dump(sample["leg_day"])
    assert data["date"] == "2026-10-01"
    [row] = data["workout_exercises"]
    assert row["sets"] == 5 and row["reps"] == 5
    assert row["exercise"]["name"] == "Squat"
    # No loop back from the association to the workout.
    assert "workout" not in row


def test_exercise_detail_includes_workouts(sample):
    data = exercise_detail_schema.dump(sample["squat"])
    assert [row["workout"]["date"] for row in data["workout_exercises"]] == [
        "2026-10-01",
        "2026-10-02",
    ]
    assert all("exercise" not in row for row in data["workout_exercises"])


# ---------- Deserialization ----------

def test_workout_schema_loads_valid_data():
    data = workout_schema.load({"date": "2026-10-20", "duration_minutes": 30})
    assert data == {"date": date(2026, 10, 20), "duration_minutes": 30, "notes": None}


def test_exercise_schema_loads_valid_data():
    payload = {"name": "Lunge", "category": "strength", "equipment_needed": True}
    assert exercise_schema.load(payload) == payload


# ---------- Schema validations ----------

@pytest.mark.parametrize(
    "payload, field",
    [
        ({"name": "  ", "category": "strength", "equipment_needed": True}, "name"),
        ({"name": "x" * 101, "category": "strength", "equipment_needed": True}, "name"),
        ({"name": "Lunge", "category": "", "equipment_needed": True}, "category"),
        ({"name": "Lunge", "category": "strength", "equipment_needed": "yes"}, "equipment_needed"),
        ({"name": "Lunge", "category": "strength", "equipment_needed": 1}, "equipment_needed"),
        ({"category": "strength", "equipment_needed": True}, "name"),
    ],
)
def test_exercise_schema_rejects_invalid_data(payload, field):
    with pytest.raises(ValidationError) as error:
        exercise_schema.load(payload)
    assert field in error.value.messages


@pytest.mark.parametrize(
    "payload, field",
    [
        ({"date": "2026-10-20", "duration_minutes": 0}, "duration_minutes"),
        ({"date": "2026-10-20", "duration_minutes": -5}, "duration_minutes"),
        ({"date": "2026-10-20", "duration_minutes": "30"}, "duration_minutes"),
        ({"date": "20/10/2026", "duration_minutes": 30}, "date"),
        ({"date": "2026-10-20", "duration_minutes": 30, "notes": "x" * 1001}, "notes"),
    ],
)
def test_workout_schema_rejects_invalid_data(payload, field):
    with pytest.raises(ValidationError) as error:
        workout_schema.load(payload)
    assert field in error.value.messages


@pytest.mark.parametrize(
    "payload, field",
    [
        ({"sets": 0, "reps": 5}, "sets"),
        ({"reps": -1}, "reps"),
        ({"duration_seconds": "60"}, "duration_seconds"),
        ({}, "_schema"),
    ],
)
def test_workout_exercise_schema_rejects_invalid_data(payload, field):
    with pytest.raises(ValidationError) as error:
        workout_exercise_schema.load(payload)
    assert field in error.value.messages
