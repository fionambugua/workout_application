#!/usr/bin/env python3

from app import app
from models import db

if __name__ == "__main__":
    with app.app_context():
        print("Seed data will be added once the models exist.")
