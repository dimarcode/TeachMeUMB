import csv
from datetime import datetime, timezone, date
from pathlib import Path
from decimal import Decimal
import os
import sys

# Add the parent directory to sys.path to make app importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from app.models import Subject

def import_subjects_data():
    with app.app_context():
        # Clear existing data
        db.session.query(Subject).delete()
        db.session.commit()
        print("Subjects table cleared.")

        data_file = Path(app.root_path) / 'data' / 'classes.csv'
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
                
                subjects = []
                row_num = 0
                
                for row in reader:
                    row_num += 1
                    if len(row) != 3:
                        print(f"Row in classes.csv {row_num} has {len(row)} columns, expected 3: {row}")
                        continue
                    
                    try:
                        subject = Subject(
                            id=int(row[0].strip()),
                            name=row[1].strip(),
                            topic=row[2].strip(),
                        )
                        subjects.append(subject)
                    except Exception as e:
                        print(f"Error in row {row_num}: {e} - {row}")
                
                if subjects:
                    db.session.bulk_save_objects(subjects)
                    db.session.commit()
                    print(f"Successfully imported {len(subjects)} subjects")
                else:
                    print("No subjects were imported")

        except Exception as e:
            print(f"Error reading {data_file}: {e}")
            import traceback
            traceback.print_exc()


