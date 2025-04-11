# filepath: app/custom/cli.py
import click
from app.custom.seed_db import import_subjects_data

@click.command('seed-db')
def seed_db_command():
    """Import initial data into the database."""
    import_subjects_data()
    click.echo("Database seeded!")

def register_cli_commands(app):
    """Register custom CLI commands."""
    app.cli.add_command(seed_db_command)