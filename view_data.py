import sqlite3
import sys

def view_table_data(table_name=None):
    """View data from SQLite database tables"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    if not table_name:
        print("\n" + "="*100)
        print("AVAILABLE TABLES")
        print("="*100)
        for idx, (tbl,) in enumerate(tables, 1):
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            count = cursor.fetchone()[0]
            print(f"{idx:2}. {tbl:<40} ({count} rows)")
        print("\nUsage: python view_data.py <table_name>")
        print("Example: python view_data.py scrap_vehicle")
        conn.close()
        return
    
    # Check if table exists
    table_names = [t[0] for t in tables]
    if table_name not in table_names:
        print(f"Error: Table '{table_name}' not found!")
        print(f"Available tables: {', '.join(table_names)}")
        conn.close()
        return
    
    # Get data from specified table
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    
    print("\n" + "="*100)
    print(f"TABLE: {table_name} ({len(rows)} rows)")
    print("="*100 + "\n")
    
    if len(rows) == 0:
        print("No data in this table.")
    else:
        # Print header
        header = " | ".join(f"{name:<20}" for name in col_names)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in rows:
            row_str = " | ".join(f"{str(val):<20}" for val in row)
            print(row_str)
    
    conn.close()
    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    table = sys.argv[1] if len(sys.argv) > 1 else None
    view_table_data(table)
