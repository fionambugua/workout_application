from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from models import db, Exercise, Workout, WorkoutExercise


# ---------- Relationships ----------

def test_workout_reaches_its_exercises(sample):
    assert list(sample["cardio"].exercises) == [sample["squat"], sample["rowing"]]


def test_exercise_reaches_its_workouts(sample):
    assert list(sample["squat"].workouts) == [sample["leg_day"], sample["cardio"]]


def test_same_exercise_has_different_metrics_per_workout(sample):
    metrics = {(we.workout_id, we.sets, we.reps) for we in sample["squat"].workout_exercises}
    assert metrics == {(sample["leg_day"].id, 5, 5), (sample["cardio"].id, 3, 12)}


def test_association_belongs_to_one_workout_and_one_exercise(sample):
    row = sample["leg_day"].workout_exercises[0]
    assert row.workout is sample["leg_day"]
    assert row.exercise is sample["squat"]


# ---------- Model validations ----------

@pytest.mark.parametrize("name", ["", "   ", None])
def test_exercise_rejects_blank_name(name):
    with pytest.raises(ValueError, match="name"):
        Exercise(name=name, category="strength", equipment_needed=False)


def test_exercise_strips_name():
    assert Exercise(name="  Squat ", category="x", equipment_needed=False).name == "Squat"


def test_exercise_rejects_non_boolean_equipment():
    with pytest.raises(ValueError, match="equipment_needed"):
        Exercise(name="Squat", category="strength", equipment_needed="yes")


@pytest.mark.parametrize("minutes", [0, -10, "30", True])
def test_workout_rejects_invalid_duration(minutes):
    with pytest.raises(ValueError, match="duration_minutes"):
        Workout(date=date(2026, 1, 1), duration_minutes=minutes)


def test_workout_rejects_non_date():
    with pytest.raises(ValueError, match="date"):
        Workout(date="2026-01-01", duration_minutes=30)


@pytest.mark.parametrize("field", ["reps", "sets", "duration_seconds"])
def test_workout_exercise_rejects_non_positive_metrics(field):
    with pytest.raises(ValueError, match=field):
        WorkoutExercise(**{field: 0})


def test_workout_exercise_allows_missing_optional_metric():
    assert WorkoutExercise(sets=3, reps=None).reps is None


# ---------- Table constraints (bypassing model validations) ----------

def insert_raw(model, **values):
    """Insert directly through the table so the @validates methods do not run."""
    db.session.execute(model.__table__.insert().values(**values))
    db.session.commit()


@pytest.mark.parametrize(
    "model, values, rule",
    [
        (Workout, {"date": date(2026, 1, 1), "duration_minutes": 0}, "duration_minutes_positive"),
        (Exercise, {"name": "  ", "category": "x", "equipment_needed": True}, "name_not_blank"),
        (Exercise, {"name": "x", "category": "", "equipment_needed": True}, "category_not_blank"),
    ],
)
def test_check_constraints_on_parent_tables(app, model, values, rule):
    with pytest.raises(IntegrityError, match=rule):
        insert_raw(model, **values)
    db.session.rollback()
    assert model.query.count() == 0


@pytest.mark.parametrize(
    "metrics, rule",
    [
        ({"reps": 0}, "reps_positive"),
        ({"sets": -1}, "sets_positive"),
        ({"duration_seconds": 0}, "duration_seconds_positive"),
        ({}, "has_metric"),
    ],
)
def test_check_constraints_on_workout_exercises(sample, metrics, rule):
    with pytest.raises(IntegrityError, match=rule):
        insert_raw(
            WorkoutExercise,
            workout_id=sample["leg_day"].id,
            exercise_id=sample["rowing"].id,
            **metrics,
        )


def test_unique_workout_exercise_pair(sample):
    with pytest.raises(IntegrityError, match="UNIQUE"):
        insert_raw(
            WorkoutExercise,
            workout_id=sample["leg_day"].id,
            exercise_id=sample["squat"].id,
            sets=1,
        )


def test_foreign_keys_are_enforced(sample):
    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        insert_raw(WorkoutExercise, workout_id=999, exercise_id=sample["squat"].id, sets=1)


def test_failed_commit_leaves_no_partial_records(sample):
    before = WorkoutExercise.query.count()
    with pytest.raises(IntegrityError):
        db.session.add(Workout(date=date(2026, 1, 1), duration_minutes=10))
        insert_raw(WorkoutExercise, workout_id=999, exercise_id=1, sets=1)
    db.session.rollback()
    assert Workout.query.count() == 2
    assert WorkoutExercise.query.count() == before
