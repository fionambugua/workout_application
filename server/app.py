from flask import Flask
from flask_migrate import Migrate

from models import db


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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
