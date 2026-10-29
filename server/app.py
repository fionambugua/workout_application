from flask import Blueprint, Flask, abort, jsonify, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from models import db, Exercise, Workout
from schemas import (
    workout_schema,
    workouts_schema,
    workout_detail_schema,
)

api = Blueprint("api", __name__)


def not_implemented():
    return jsonify({"error": "Not implemented yet."}), 501


def get_json_body():
    """Return the request body as a dict, or stop with a 400 error."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Request body must be a JSON object.")
    return data


def get_or_404(model, id):
    record = db.session.get(model, id)
    if record is None:
        abort(404, description=f"{model.__name__} {id} not found.")
    return record


def build(model, **fields):
    """Create a model instance, turning model validation errors into a 400."""
    try:
        return model(**fields)
    except ValueError as error:
        # Raised by the @validates methods in models.py.
        abort(400, description=str(error))


# ---------- Workouts ----------

@api.get("/workouts")
def list_workouts():
    workouts = Workout.query.order_by(Workout.date, Workout.id).all()
    return jsonify(workouts_schema.dump(workouts)), 200


@api.get("/workouts/<int:id>")
def get_workout(id):
    workout = get_or_404(Workout, id)
    return jsonify(workout_detail_schema.dump(workout)), 200


@api.post("/workouts")
def create_workout():
    data = workout_schema.load(get_json_body())
    workout = build(Workout, **data)
    db.session.add(workout)
    db.session.commit()
    return jsonify(workout_schema.dump(workout)), 201


@api.delete("/workouts/<int:id>")
def delete_workout(id):
    workout = get_or_404(Workout, id)
    # The relationship cascade also deletes this workout's WorkoutExercise rows.
    db.session.delete(workout)
    db.session.commit()
    return "", 204


# ---------- Exercises ----------

@api.get("/exercises")
def list_exercises():
    return not_implemented()


@api.get("/exercises/<int:id>")
def get_exercise(id):
    return not_implemented()


@api.post("/exercises")
def create_exercise():
    return not_implemented()


@api.delete("/exercises/<int:id>")
def delete_exercise(id):
    return not_implemented()


# ---------- Workout exercises ----------

@api.post("/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises")
def add_exercise_to_workout(workout_id, exercise_id):
    return not_implemented()


# ---------- Error handling ----------
# Every error response has the shape {"error": "...", "details": {...}}.

@api.app_errorhandler(ValidationError)
def handle_schema_error(error):
    return jsonify({"error": "Validation failed.", "details": error.messages}), 400


@api.app_errorhandler(IntegrityError)
def handle_integrity_error(error):
    db.session.rollback()
    if "UNIQUE" in str(error.orig):
        return jsonify({"error": "This record already exists."}), 409
    return jsonify({"error": "The data breaks a database rule."}), 400


@api.app_errorhandler(HTTPException)
def handle_http_error(error):
    return jsonify({"error": error.description}), error.code


@api.app_errorhandler(Exception)
def handle_unexpected_error(error):
    db.session.rollback()
    return jsonify({"error": "An unexpected server error occurred."}), 500


def create_app(test_config=None):
    """Build and configure the Flask application."""
    app = Flask(__name__)

    # A relative SQLite path is stored in the Flask instance folder:
    # server/instance/app.db
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.json.compact = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    Migrate(app, db, render_as_batch=True)
    app.register_blueprint(api)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
