from app import app
from app.custom.seed_db import import_subjects_data, import_locations_data

@app.cli.command("seed-db")
def seed_db_command():
    """Import initial data into the database."""
    import_subjects_data()
    import_locations_data()
    print("Database seeded!")