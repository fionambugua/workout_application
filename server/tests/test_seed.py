from models import db, Exercise, Workout, WorkoutExercise
from seed import clear_data, seed_data


def run_seed():
    clear_data()
    seed_data()
    db.session.commit()


def test_seed_creates_all_three_models(app):
    run_seed()
    assert Exercise.query.count() == 6
    assert Workout.query.count() == 4
    assert WorkoutExercise.query.count() == 10


def test_seed_can_be_rerun_without_duplicates(app):
    run_seed()
    run_seed()
    assert Exercise.query.count() == 6
    assert Workout.query.count() == 4
    assert WorkoutExercise.query.count() == 10


def test_seeded_relationships_work(app):
    run_seed()
    squat = Exercise.query.filter_by(name="Squat").one()
    assert len(list(squat.workouts)) == 2
