import os

from flask_migrate import upgrade
from sqlalchemy import inspect

from app import create_app
from models import db


def test_migrations_build_a_clean_database_matching_the_models(tmp_path):
    database = tmp_path / "migrated.db"
    app = create_app({"SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}"})
    migrations = os.path.join(os.path.dirname(__file__), "..", "migrations")

    with app.app_context():
        upgrade(directory=migrations)
        inspector = inspect(db.engine)

        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "exercises",
            "workouts",
            "workout_exercises",
        }
        for table in db.metadata.sorted_tables:
            columns = {column["name"] for column in inspector.get_columns(table.name)}
            assert columns == set(table.columns.keys())

        foreign_keys = inspector.get_foreign_keys("workout_exercises")
        assert {fk["referred_table"] for fk in foreign_keys} == {"workouts", "exercises"}
        checks = {c["name"] for c in inspector.get_check_constraints("workout_exercises")}
        assert "ck_workout_exercises_has_metric" in checks
        db.engine.dispose()
