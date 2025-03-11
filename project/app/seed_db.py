import csv
from datetime import datetime, timezone, date
from pathlib import Path
from decimal import Decimal
import os
import sys

# Add the parent directory to sys.path to make app importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from app.models import Customer, Item, Order

def import_customer_data():
    with app.app_context():
        # Clear existing data
        db.session.query(Customer).delete()
        db.session.commit()
        print("Customer table cleared.")

        data_file = Path(app.root_path) / 'data' / 'customers.csv'
        print(f"Looking for data file at: {data_file}")
        
        if not data_file.exists():
            print(f"Error: File does not exist at {data_file}")
            return

        try:
            with open(data_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # Skip header if it exists
                # Uncomment if your CSV has a header row
                # next(reader, None)
                
                customers = []
                row_num = 0
                
                for row in reader:
                    row_num += 1
                    if len(row) != 9:
                        print(f"Row in customers.csv {row_num} has {len(row)} columns, expected 9: {row}")
                        continue
                    
                    try:
                        customer = Customer(
                            id=int(row[0].strip()),
                            first_name=row[1].strip(),
                            last_name=row[2].strip(),
                            address=row[3].strip(),
                            city=row[4].strip(),
                            state=row[5].strip(),
                            zip=row[6].strip(),
                            phone=row[7].strip(),
                            email=row[8].strip()
                        )
                        customers.append(customer)
                    except Exception as e:
                        print(f"Error in row {row_num}: {e} - {row}")
                
                if customers:
                    db.session.bulk_save_objects(customers)
                    db.session.commit()
                    print(f"Successfully imported {len(customers)} customers")
                else:
                    print("No customers were imported")

        except Exception as e:
            print(f"Error reading {data_file}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    import_customer_data()

# IMPORT ITEM DATA
def import_item_data():
    with app.app_context():
        # Clear existing data
        db.session.query(Item).delete()
        db.session.commit()
        print("Item table cleared.")

        data_file = Path(app.root_path) / 'data' / 'items.csv'
        print(f"Looking for data file at: {data_file}")
        
        if not data_file.exists():
            print(f"Error: File does not exist at {data_file}")
            return

        try:
            with open(data_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # Skip header if it exists
                # Uncomment if your CSV has a header row
                # next(reader, None)
                
                items = []
                row_num = 0
                
                for row in reader:
                    row_num += 1
                    if len(row) != 3:
                        print(f"Row in .items.csv {row_num} has {len(row)} columns, expected 3: {row}")
                        continue
                    
                    try:
                        item = Item(
                            id=int(row[0].strip()),
                            item_name=row[1].strip(),
                            price=Decimal(row[2].strip())  # Use Decimal for precision
                        )
                        items.append(item)
                    except Exception as e:
                        print(f"Error in row {row_num}: {e} - {row}")
                
                if items:
                    db.session.bulk_save_objects(items)
                    db.session.commit()
                    print(f"Successfully imported {len(items)} items")
                else:
                    print("No items were imported")

        except Exception as e:
            print(f"Error reading {data_file}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    import_item_data()

# IMPORT ORDER DATA
def import_order_data():
    with app.app_context():
        # Clear existing data
        db.session.query(Order).delete()
        db.session.commit()
        print("Order table cleared.")

        data_file = Path(app.root_path) / 'data' / 'orders.csv'
        print(f"Looking for data file at: {data_file}")
        
        if not data_file.exists():
            print(f"Error: File does not exist at {data_file}")
            return

        try:
            with open(data_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # Skip header if it exists
                # Uncomment if your CSV has a header row
                # next(reader, None)
                
                orders = []
                row_num = 0
                
                for row in reader:
                    row_num += 1
                    if len(row) != 4:
                        print(f"Row in .orders.csv {row_num} has {len(row)} columns, expected 3: {row}")
                        continue
                    
                    try:
                        order = Order(
                            order_id=int(row[0].strip()),
                            customer_id=int(row[1].strip()),
                            order_number=int(row[2].strip()),
                            date=datetime.strptime(row[3].strip(), "%Y-%m-%d").date()
                            )
                        orders.append(order)
                    except Exception as e:
                        print(f"Error in row {row_num}: {e} - {row}")
                
                if orders:
                    db.session.bulk_save_objects(orders)
                    db.session.commit()
                    print(f"Successfully imported {len(orders)} orders")
                else:
                    print("No items were imported")

        except Exception as e:
            print(f"Error reading {data_file}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    import_order_data()