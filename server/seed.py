#!/usr/bin/env python3

from datetime import date

from app import app
from models import db, Exercise, Workout, WorkoutExercise


def clear_data():
    """Remove existing rows, children first so foreign keys stay valid."""
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()


def seed_data():
    squat = Exercise(name="Squat", category="strength", equipment_needed=False)
    push_up = Exercise(name="Push-up", category="strength", equipment_needed=False)
    deadlift = Exercise(name="Deadlift", category="strength", equipment_needed=True)
    running = Exercise(name="Running", category="cardio", equipment_needed=False)
    plank = Exercise(name="Plank", category="core", equipment_needed=False)
    rowing = Exercise(name="Rowing", category="cardio", equipment_needed=True)

    leg_day = Workout(
        date=date(2026, 10, 1), duration_minutes=60, notes="Heavy leg session."
    )
    upper_body = Workout(
        date=date(2026, 10, 3), duration_minutes=45, notes="Push focus."
    )
    cardio_day = Workout(
        date=date(2026, 10, 5), duration_minutes=40, notes="Steady-state cardio."
    )
    full_body = Workout(date=date(2026, 10, 7), duration_minutes=50)

    workout_exercises = [
        WorkoutExercise(workout=leg_day, exercise=squat, sets=5, reps=5),
        WorkoutExercise(workout=leg_day, exercise=deadlift, sets=3, reps=5),
        WorkoutExercise(workout=leg_day, exercise=plank, sets=3, duration_seconds=60),
        WorkoutExercise(workout=upper_body, exercise=push_up, sets=4, reps=15),
        WorkoutExercise(workout=upper_body, exercise=plank, sets=2, duration_seconds=90),
        WorkoutExercise(workout=cardio_day, exercise=running, duration_seconds=1800),
        WorkoutExercise(workout=cardio_day, exercise=rowing, duration_seconds=600),
        WorkoutExercise(workout=full_body, exercise=squat, sets=3, reps=12),
        WorkoutExercise(workout=full_body, exercise=push_up, sets=3, reps=12),
        WorkoutExercise(workout=full_body, exercise=rowing, duration_seconds=300),
    ]

    # Adding the association rows also adds their related workouts and exercises.
    db.session.add_all(workout_exercises)


if __name__ == "__main__":
    with app.app_context():
        try:
            print("Clearing existing data...")
            clear_data()
            print("Seeding exercises, workouts and workout exercises...")
            seed_data()
            db.session.commit()
        except Exception:
            db.session.rollback()
            print("Seeding failed; all changes were rolled back.")
            raise

        print(
            f"Done: {Exercise.query.count()} exercises, "
            f"{Workout.query.count()} workouts, "
            f"{WorkoutExercise.query.count()} workout exercises."
        )
