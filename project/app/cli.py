from app import app
from app.seed_db import import_subjects_data

@app.cli.command("seed-db")
def seed_db_command():
    """Import initial data into the database."""
    import_subjects_data()
    print("Database seeded!")