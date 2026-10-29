# Flask SQLAlchemy Workout Application Backend

A REST API for tracking workouts. Users can create, view and delete **workouts** and
reusable **exercises**, and add an exercise to a workout along with the sets, reps
and/or duration for that particular session.

## Features

- **Workouts**: a session with a date, a length in minutes and optional notes.
- **Exercises**: reusable movements such as squats, push-ups or running, each with a
  category and whether it needs equipment.
- **Workout exercises**: an association model that links a workout to an exercise and
  stores session-specific `sets`, `reps` and `duration_seconds`. The same exercise can
  appear in many workouts with different numbers each time.
- Validation at three layers: Marshmallow schemas (request data), SQLAlchemy
  `@validates` methods (model data) and database `CHECK`/`UNIQUE`/foreign key
  constraints (stored data).
- Marshmallow serialization with nested detail views that never recurse.
- Consistent JSON error responses with appropriate HTTP status codes.
- A repeatable seed script and an automated pytest suite.

## Technology stack

| Tool | Version |
| --- | --- |
| Python | 3.12 (assignment minimum: 3.8.13) |
| Flask | 2.2.2 |
| Werkzeug | 2.2.2 |
| Flask-SQLAlchemy | 3.0.3 |
| Flask-Migrate | 3.1.0 (Alembic) |
| Marshmallow | 3.20.1 |
| importlib-metadata | 6.0.0 |
| importlib-resources | 5.10.0 |
| ipdb | 0.13.9 |
| pytest | dev dependency |
| SQLite | development database |
| Pipenv | environment and dependency management |

## Project structure

```text
workout_application/
├── README.md
├── .gitignore
├── Pipfile               # dependencies
├── Pipfile.lock
└── server/
    ├── app.py            # app factory, routes and error handlers
    ├── models.py         # Exercise, Workout, WorkoutExercise, validations, constraints
    ├── schemas.py        # Marshmallow schemas and schema validations
    ├── seed.py           # resets and seeds the database
    ├── pytest.ini        # test configuration
    ├── migrations/       # Flask-Migrate / Alembic migration history
    ├── tests/            # pytest suite
    └── instance/
        └── app.db        # SQLite database (created locally, not committed)
```

## Installation

```bash
git clone git@github.com:fionambugua/workout_application.git
cd workout_application
pipenv install --dev
pipenv shell
```

`--dev` also installs pytest. If Pipenv reports that it is "running within a virtual
environment" (for example a pyenv or another project's environment), run
`PIPENV_IGNORE_VIRTUALENVS=1 pipenv install --dev` so the project gets its own.

## Database setup

All Flask commands are run from the `server/` directory, where Flask finds `app.py`
automatically.

```bash
cd server
flask db upgrade     # creates server/instance/app.db with all three tables
python seed.py       # clears and reseeds sample data
```

The migration folder is already initialized, so **do not** run `flask db init` again.
After changing a model, create and apply a new migration:

```bash
flask db migrate -m "describe the change"
flask db upgrade
```

`seed.py` deletes existing rows (association rows first) and inserts 6 exercises,
4 workouts and 10 workout exercises. It can be rerun safely; it never duplicates data.
If seeding fails, every change is rolled back.

## Running the server

```bash
cd server
python app.py                      # http://127.0.0.1:5555 with debug mode on
# or
flask --debug run --port 5555
```

## API endpoints

| Method | Endpoint | Purpose | Success |
| --- | --- | --- | --- |
| GET | `/workouts` | List all workouts | 200 |
| GET | `/workouts/<id>` | One workout with its exercises and their sets/reps/duration | 200 |
| POST | `/workouts` | Create a workout | 201 |
| DELETE | `/workouts/<id>` | Delete a workout and its workout exercises | 204 |
| GET | `/exercises` | List all exercises | 200 |
| GET | `/exercises/<id>` | One exercise with the workouts it appears in | 200 |
| POST | `/exercises` | Create an exercise | 201 |
| DELETE | `/exercises/<id>` | Delete an exercise and its workout exercises | 204 |
| POST | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout | 201 |

Request bodies must be JSON objects (send `Content-Type: application/json`).
Deleting a workout or exercise also deletes the association rows that use it, so no
orphaned records remain. The other side of each association is kept.

### Request bodies

**POST `/workouts`**

| Field | Type | Rules |
| --- | --- | --- |
| `date` | string `YYYY-MM-DD` | required |
| `duration_minutes` | integer | required, at least 1 |
| `notes` | string or null | optional, at most 1000 characters |

**POST `/exercises`**

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | required, not blank, at most 100 characters (surrounding spaces are trimmed) |
| `category` | string | required, not blank, at most 50 characters |
| `equipment_needed` | boolean | required, must be JSON `true` or `false` |

**POST `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises`**

| Field | Type | Rules |
| --- | --- | --- |
| `sets` | integer or null | optional, at least 1 |
| `reps` | integer or null | optional, at least 1 |
| `duration_seconds` | integer or null | optional, at least 1 |

At least one of the three must be given. The workout and exercise IDs come from the
URL, so they are rejected in the body. An exercise can be added to a given workout once.

## Example requests and responses

**Create a workout**

```http
POST /workouts
Content-Type: application/json

{"date": "2026-10-20", "duration_minutes": 45, "notes": "Upper body"}
```

`201 Created`

```json
{"id": 5, "date": "2026-10-20", "duration_minutes": 45, "notes": "Upper body"}
```

**Create an exercise**

```http
POST /exercises
Content-Type: application/json

{"name": "Lunge", "category": "strength", "equipment_needed": false}
```

`201 Created`

```json
{"id": 7, "name": "Lunge", "category": "strength", "equipment_needed": false}
```

**Add the exercise to the workout**

```http
POST /workouts/5/exercises/7/workout_exercises
Content-Type: application/json

{"sets": 3, "reps": 12}
```

`201 Created`

```json
{
  "id": 11,
  "workout_id": 5,
  "exercise_id": 7,
  "sets": 3,
  "reps": 12,
  "duration_seconds": null,
  "workout": {"id": 5, "date": "2026-10-20", "duration_minutes": 45, "notes": "Upper body"},
  "exercise": {"id": 7, "name": "Lunge", "category": "strength", "equipment_needed": false}
}
```

**Show a workout** (`GET /workouts/5`, `200 OK`)

```json
{
  "id": 5,
  "date": "2026-10-20",
  "duration_minutes": 45,
  "notes": "Upper body",
  "workout_exercises": [
    {
      "id": 11,
      "workout_id": 5,
      "exercise_id": 7,
      "sets": 3,
      "reps": 12,
      "duration_seconds": null,
      "exercise": {"id": 7, "name": "Lunge", "category": "strength", "equipment_needed": false}
    }
  ]
}
```

`GET /exercises/<id>` has the same shape, except that each item in
`workout_exercises` contains a `workout` instead of an `exercise`.

**Delete** (`DELETE /workouts/5`): `204 No Content` with an empty body.

## Validation and error handling

| Layer | Where | Rules |
| --- | --- | --- |
| Schema validations | `server/schemas.py` | required fields; names and categories not blank and length-limited; strict integers at least 1; strict booleans; valid ISO dates; notes length; at least one workout exercise metric; unknown fields rejected |
| Model validations | `@validates` in `server/models.py` | name/category non-empty (trimmed); `equipment_needed` is a boolean; `date` is a date; `duration_minutes`, `sets`, `reps`, `duration_seconds` are positive whole numbers (metrics may be null) |
| Table constraints | `__table_args__` in `server/models.py` | `duration_minutes > 0`; name and category not blank; `sets`, `reps`, `duration_seconds` null or `> 0`; at least one metric present; `UNIQUE(workout_id, exercise_id)`; foreign keys with `ON DELETE CASCADE` (SQLite foreign keys are switched on for every connection) |

Every error response is JSON with an `error` message. Validation errors also include
`details` listing each problem by field:

```json
{
  "error": "Validation failed.",
  "details": {"duration_minutes": ["Must be greater than or equal to 1."]}
}
```

| Status | When |
| --- | --- |
| 400 | invalid or missing fields, non-JSON body, or data that breaks a database rule |
| 404 | the workout or exercise ID does not exist, or an unknown URL |
| 405 | the HTTP method is not supported for that URL |
| 409 | the exercise is already part of that workout |
| 500 | unexpected server error (a generic message; no traceback is exposed) |

Failed database operations are rolled back, so a rejected request never leaves
partial records behind.

## Running the tests

```bash
cd server
pytest           # or: pipenv run pytest
```

The suite (80 tests) uses a fresh in-memory database for each test and covers the
models, relationships, model validations, table constraints, schemas, every endpoint
(success, missing records, invalid input), cascade deletes, duplicate associations,
rollbacks, the seed script and applying migrations to a clean database.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Error: Could not locate a Flask application` | Run Flask commands from `server/`, or set `export FLASK_APP=app.py`. |
| `no such table: workouts` | Run `flask db upgrade` from `server/` before seeding or starting the app. |
| Want a completely fresh database | Delete `server/instance/app.db`, then `flask db upgrade` and `python seed.py`. |
| `Target database is not up to date` when migrating | Run `flask db upgrade` first, then `flask db migrate`. |
| `Address already in use` on port 5555 | Stop the other process, or run `flask run --port 5556`. |
| Every POST returns "Request body must be a JSON object." | Send a JSON body with the `Content-Type: application/json` header (in Postman: Body → raw → JSON). |
| `equipment_needed` rejected | Use JSON `true`/`false`, not `"true"`, `1` or `"yes"`. |
| Pipenv uses the wrong environment | Use `PIPENV_IGNORE_VIRTUALENVS=1 pipenv install --dev`. |
| Many `DeprecationWarning`s from Werkzeug | Werkzeug 2.2.2 (pinned by the assignment) uses features deprecated in Python 3.12. They are harmless and filtered out in `pytest.ini`. |
