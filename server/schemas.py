from marshmallow import Schema, fields


class ExerciseSchema(Schema):
    """Serializes an exercise and validates new exercise data."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    category = fields.Str(required=True)
    equipment_needed = fields.Bool(required=True)


class WorkoutSchema(Schema):
    """Serializes a workout and validates new workout data."""

    id = fields.Int(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Int(required=True)
    notes = fields.Str(allow_none=True, load_default=None)


class WorkoutExerciseSchema(Schema):
    """Serializes an association row and validates its metrics."""

    id = fields.Int(dump_only=True)
    # The workout and exercise IDs come from the URL, not the request body.
    workout_id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    reps = fields.Int(allow_none=True, load_default=None)
    sets = fields.Int(allow_none=True, load_default=None)
    duration_seconds = fields.Int(allow_none=True, load_default=None)

    workout = fields.Nested(WorkoutSchema, dump_only=True)
    exercise = fields.Nested(ExerciseSchema, dump_only=True)


class WorkoutDetailSchema(WorkoutSchema):
    """A workout with its exercises and the workout-specific metrics.

    The nested rows leave out "workout" so the output never loops back on itself.
    """

    workout_exercises = fields.List(
        fields.Nested(WorkoutExerciseSchema(exclude=("workout",))), dump_only=True
    )


class ExerciseDetailSchema(ExerciseSchema):
    """An exercise with the workouts it appears in."""

    workout_exercises = fields.List(
        fields.Nested(WorkoutExerciseSchema(exclude=("exercise",))), dump_only=True
    )


exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
exercise_detail_schema = ExerciseDetailSchema()

workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_detail_schema = WorkoutDetailSchema()

workout_exercise_schema = WorkoutExerciseSchema()
