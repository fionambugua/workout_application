from datetime import date

import pytest

from app import create_app
from models import db, Exercise, Workout, WorkoutExercise


@pytest.fixture
def app():
    """A fresh app backed by an in-memory database for every test."""
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample(app):
    """Two workouts sharing one exercise, plus an unused exercise."""
    squat = Exercise(name="Squat", category="strength", equipment_needed=False)
    rowing = Exercise(name="Rowing", category="cardio", equipment_needed=True)
    unused = Exercise(name="Plank", category="core", equipment_needed=False)
    leg_day = Workout(date=date(2026, 10, 1), duration_minutes=60, notes="Legs")
    cardio = Workout(date=date(2026, 10, 2), duration_minutes=30)
    db.session.add_all(
        [
            WorkoutExercise(workout=leg_day, exercise=squat, sets=5, reps=5),
            WorkoutExercise(workout=cardio, exercise=squat, sets=3, reps=12),
            WorkoutExercise(workout=cardio, exercise=rowing, duration_seconds=600),
            unused,
        ]
    )
    db.session.commit()
    return {
        "squat": squat,
        "rowing": rowing,
        "unused": unused,
        "leg_day": leg_day,
        "cardio": cardio,
    }
