import pytest

from models import db, Exercise, Workout, WorkoutExercise


def association_url(workout_id, exercise_id):
    return f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises"


# ---------- Workouts ----------

def test_list_workouts_empty(client):
    response = client.get("/workouts")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_workouts(client, sample):
    response = client.get("/workouts")
    assert response.status_code == 200
    assert [w["date"] for w in response.get_json()] == ["2026-10-01", "2026-10-02"]


def test_get_workout_with_exercises(client, sample):
    response = client.get(f"/workouts/{sample['cardio'].id}")
    assert response.status_code == 200
    rows = response.get_json()["workout_exercises"]
    assert {row["exercise"]["name"] for row in rows} == {"Squat", "Rowing"}
    rowing = next(row for row in rows if row["exercise"]["name"] == "Rowing")
    assert rowing["duration_seconds"] == 600


def test_get_missing_workout(client):
    response = client.get("/workouts/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Workout 999 not found."}


def test_create_workout(client):
    payload = {"date": "2026-10-20", "duration_minutes": 30, "notes": "Easy"}
    response = client.post("/workouts", json=payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["id"] and body["duration_minutes"] == 30
    assert db.session.get(Workout, body["id"]).notes == "Easy"


@pytest.mark.parametrize(
    "payload",
    [{"date": "2026-10-20", "duration_minutes": 0}, {"duration_minutes": 30}, {}],
)
def test_create_workout_invalid(client, payload):
    response = client.post("/workouts", json=payload)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Validation failed."
    assert Workout.query.count() == 0


def test_create_workout_requires_json_object(client):
    response = client.post("/workouts", data="not json")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Request body must be a JSON object."}


def test_delete_workout_removes_its_associations(client, sample):
    workout_id = sample["cardio"].id
    response = client.delete(f"/workouts/{workout_id}")
    assert response.status_code == 204
    assert db.session.get(Workout, workout_id) is None
    assert WorkoutExercise.query.filter_by(workout_id=workout_id).count() == 0
    # The exercises themselves are kept.
    assert Exercise.query.count() == 3


def test_delete_missing_workout(client):
    assert client.delete("/workouts/999").status_code == 404


# ---------- Exercises ----------

def test_list_exercises_empty(client):
    response = client.get("/exercises")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_exercises(client, sample):
    response = client.get("/exercises")
    assert response.status_code == 200
    assert [e["name"] for e in response.get_json()] == ["Plank", "Rowing", "Squat"]


def test_get_exercise_with_workouts(client, sample):
    response = client.get(f"/exercises/{sample['squat'].id}")
    assert response.status_code == 200
    rows = response.get_json()["workout_exercises"]
    assert [row["workout"]["id"] for row in rows] == [
        sample["leg_day"].id,
        sample["cardio"].id,
    ]


def test_get_missing_exercise(client):
    response = client.get("/exercises/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Exercise 999 not found."}


def test_create_exercise(client):
    payload = {"name": " Lunge ", "category": "strength", "equipment_needed": False}
    response = client.post("/exercises", json=payload)
    assert response.status_code == 201
    assert response.get_json()["name"] == "Lunge"
    assert Exercise.query.count() == 1


def test_create_exercise_invalid(client):
    payload = {"name": "", "category": "strength", "equipment_needed": "no"}
    response = client.post("/exercises", json=payload)
    assert response.status_code == 400
    assert set(response.get_json()["details"]) == {"name", "equipment_needed"}
    assert Exercise.query.count() == 0


def test_delete_exercise_removes_its_associations(client, sample):
    exercise_id = sample["squat"].id
    response = client.delete(f"/exercises/{exercise_id}")
    assert response.status_code == 204
    assert db.session.get(Exercise, exercise_id) is None
    assert WorkoutExercise.query.filter_by(exercise_id=exercise_id).count() == 0
    # The workouts themselves are kept.
    assert Workout.query.count() == 2


def test_delete_missing_exercise(client):
    assert client.delete("/exercises/999").status_code == 404


# ---------- Workout exercises ----------

def test_add_exercise_to_workout(client, sample):
    url = association_url(sample["leg_day"].id, sample["rowing"].id)
    response = client.post(url, json={"sets": 2, "duration_seconds": 300})
    assert response.status_code == 201
    body = response.get_json()
    assert body["workout_id"] == sample["leg_day"].id
    assert body["exercise"]["name"] == "Rowing"
    assert (body["sets"], body["reps"], body["duration_seconds"]) == (2, None, 300)
    assert sample["rowing"] in sample["leg_day"].exercises


def test_add_duplicate_exercise_to_workout(client, sample):
    before = WorkoutExercise.query.count()
    url = association_url(sample["leg_day"].id, sample["squat"].id)
    response = client.post(url, json={"sets": 1})
    assert response.status_code == 409
    assert WorkoutExercise.query.count() == before
    # The session was rolled back, so later requests still work.
    assert client.get("/workouts").status_code == 200


@pytest.mark.parametrize(
    "workout_id, exercise_id, missing", [(999, None, "Workout"), (None, 999, "Exercise")]
)
def test_add_exercise_with_missing_records(client, sample, workout_id, exercise_id, missing):
    url = association_url(
        workout_id or sample["leg_day"].id, exercise_id or sample["rowing"].id
    )
    response = client.post(url, json={"sets": 1})
    assert response.status_code == 404
    assert response.get_json()["error"].startswith(missing)


@pytest.mark.parametrize("payload", [{}, {"reps": 0}, {"sets": "3"}, {"workout_id": 1, "sets": 1}])
def test_add_exercise_invalid_metrics(client, sample, payload):
    before = WorkoutExercise.query.count()
    url = association_url(sample["leg_day"].id, sample["rowing"].id)
    response = client.post(url, json=payload)
    assert response.status_code == 400
    assert WorkoutExercise.query.count() == before


# ---------- General errors ----------

def test_unsupported_method(client):
    response = client.put("/workouts/1")
    assert response.status_code == 405
    assert "error" in response.get_json()


def test_unexpected_error_returns_safe_500(app, client, monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr("app.workouts_schema.dump", explode)
    response = client.get("/workouts")
    assert response.status_code == 500
    assert response.get_json() == {"error": "An unexpected server error occurred."}
