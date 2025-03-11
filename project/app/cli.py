from app import app
from app.seed_db import import_customer_data, import_item_data, import_order_data

@app.cli.command("seed-db")
def seed_db_command():
    """Import initial data into the database."""
    import_customer_data()
    import_item_data()
    import_order_data()
    print("Database seeded!")