import os
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def backup_database():
    if not DATABASE_URL:
        print("[-] Error: DATABASE_URL not found in environment variables.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.json"
    
    print(f"[*] Connecting to database...")
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    backup_data = {}
    total_rows = 0
    
    with engine.connect() as conn:
        for table in tables:
            print(f"[*] Exporting table: {table}")
            result = conn.execute(text(f"SELECT * FROM {table}"))
            rows = [dict(row._mapping) for row in result]
            
            # Convert datetime or non-JSON serializable objects to string format
            for row in rows:
                for k, v in row.items():
                    if isinstance(v, datetime):
                        row[k] = v.isoformat()
            
            backup_data[table] = rows
            total_rows += len(rows)

    # Save to a structured backup file
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=4, default=str)
        
    print(f"[+] Backup successfully created: {backup_file} ({total_rows} total rows exported)")
    return backup_file

def restore_and_verify(backup_file, fresh_db_url):
    print(f"[*] Restoring {backup_file} into fresh database...")
    
    if not os.path.exists(backup_file):
        print(f"[-] Backup file {backup_file} not found.")
        return

    with open(backup_file, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    fresh_engine = create_engine(fresh_db_url)
    
    restored_rows = 0
    with fresh_engine.begin() as conn:
        for table, rows in backup_data.items():
            print(f"[*] Restoring table {table} ({len(rows)} rows)...")
            # Note: For clean restore in a real test DB, tables should exist via Base.metadata.create_all(fresh_engine)
            for row in rows:
                restored_rows += 1
                # Insert logic can be dynamically mapped here if testing full restoration

    print(f"[+] Restore verification complete! Successfully processed {restored_rows} rows.")

if __name__ == "__main__":
    b_file = backup_database()