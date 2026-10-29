from flask import Blueprint, Flask, jsonify
from flask_migrate import Migrate

from models import db

api = Blueprint("api", __name__)


def not_implemented():
    return jsonify({"error": "Not implemented yet."}), 501


# ---------- Workouts ----------

@api.get("/workouts")
def list_workouts():
    return not_implemented()


@api.get("/workouts/<int:id>")
def get_workout(id):
    return not_implemented()


@api.post("/workouts")
def create_workout():
    return not_implemented()


@api.delete("/workouts/<int:id>")
def delete_workout(id):
    return not_implemented()


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
