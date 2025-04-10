from flask import current_app
from app.custom.seed_db import import_subjects_data

def seed_db_command():
    """Import initial data into the database."""
    import_subjects_data()
    print("Database seeded!")