from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

# A naming convention gives every constraint a predictable name, which
# Alembic needs in order to create (and later drop) constraints in SQLite.
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign keys unless this is switched on per connection."""
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def require_positive_int(key, value, allow_none=False):
    """Shared model validation for whole-number fields that must be above zero."""
    if value is None and allow_none:
        return value
    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{key} must be a positive whole number.")
    return value


class Exercise(db.Model):
    """A reusable exercise, such as squats, push-ups or running."""

    __tablename__ = "exercises"
    __table_args__ = (
        db.CheckConstraint("length(trim(name)) > 0", name="name_not_blank"),
        db.CheckConstraint("length(trim(category)) > 0", name="category_not_blank"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    # Deleting an exercise also deletes the rows that link it to workouts.
    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan"
    )
    workouts = association_proxy("workout_exercises", "workout")

    @validates("name", "category")
    def validate_text(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string.")
        return value.strip()

    @validates("equipment_needed")
    def validate_equipment_needed(self, key, value):
        if not isinstance(value, bool):
            raise ValueError("equipment_needed must be true or false.")
        return value

    def __repr__(self):
        return f"<Exercise {self.id}: {self.name}>"


class Workout(db.Model):
    """A single workout session."""

    __tablename__ = "workouts"
    __table_args__ = (
        db.CheckConstraint("duration_minutes > 0", name="duration_minutes_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    # Deleting a workout also deletes the rows that link it to exercises.
    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="workout", cascade="all, delete-orphan"
    )
    exercises = association_proxy("workout_exercises", "exercise")

    @validates("date")
    def validate_date(self, key, value):
        if not isinstance(value, date):
            raise ValueError("date must be a valid date.")
        return value

    @validates("duration_minutes")
    def validate_duration_minutes(self, key, value):
        return require_positive_int(key, value)

    def __repr__(self):
        return f"<Workout {self.id}: {self.date}>"


class WorkoutExercise(db.Model):
    """Joins a workout to an exercise and stores the workout-specific metrics."""

    __tablename__ = "workout_exercises"
    __table_args__ = (
        # The same exercise can only be added to a given workout once.
        db.UniqueConstraint("workout_id", "exercise_id"),
        # Metrics are optional, but any value that is supplied must be positive.
        db.CheckConstraint("reps IS NULL OR reps > 0", name="reps_positive"),
        db.CheckConstraint("sets IS NULL OR sets > 0", name="sets_positive"),
        db.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="duration_seconds_positive",
        ),
        db.CheckConstraint(
            "reps IS NOT NULL OR sets IS NOT NULL OR duration_seconds IS NOT NULL",
            name="has_metric",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id = db.Column(
        db.Integer, db.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    @validates("reps", "sets", "duration_seconds")
    def validate_metric(self, key, value):
        return require_positive_int(key, value, allow_none=True)

    def __repr__(self):
        return (
            f"<WorkoutExercise workout={self.workout_id} "
            f"exercise={self.exercise_id}>"
        )
