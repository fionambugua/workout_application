from marshmallow import Schema, ValidationError, fields, validate, validates_schema


def not_blank(value):
    """Reject strings that are empty or only whitespace."""
    if not value.strip():
        raise ValidationError("Must not be blank.")


def StrictBool(**kwargs):
    """Only real JSON true/false are accepted, so "yes" or 1 are not converted."""
    return fields.Bool(truthy={True}, falsy={False}, **kwargs)


def PositiveInt(**kwargs):
    """strict=True rejects strings such as "5"; Range rejects zero and negatives."""
    return fields.Int(strict=True, validate=validate.Range(min=1), **kwargs)


class ExerciseSchema(Schema):
    """Serializes an exercise and validates new exercise data."""

    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True, validate=[validate.Length(min=1, max=100), not_blank]
    )
    category = fields.Str(
        required=True, validate=[validate.Length(min=1, max=50), not_blank]
    )
    equipment_needed = StrictBool(required=True)


class WorkoutSchema(Schema):
    """Serializes a workout and validates new workout data."""

    id = fields.Int(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = PositiveInt(required=True)
    notes = fields.Str(
        allow_none=True, load_default=None, validate=validate.Length(max=1000)
    )


class WorkoutExerciseSchema(Schema):
    """Serializes an association row and validates its metrics."""

    id = fields.Int(dump_only=True)
    # The workout and exercise IDs come from the URL, not the request body.
    workout_id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    reps = PositiveInt(allow_none=True, load_default=None)
    sets = PositiveInt(allow_none=True, load_default=None)
    duration_seconds = PositiveInt(allow_none=True, load_default=None)

    workout = fields.Nested(WorkoutSchema, dump_only=True)
    exercise = fields.Nested(ExerciseSchema, dump_only=True)

    @validates_schema
    def validate_has_metric(self, data, **kwargs):
        if all(data.get(key) is None for key in ("reps", "sets", "duration_seconds")):
            raise ValidationError(
                "Provide at least one of reps, sets or duration_seconds."
            )


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
