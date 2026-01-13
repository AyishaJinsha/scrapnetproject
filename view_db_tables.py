import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print("\n" + "="*100)
print(f"DATABASE TABLES (Total: {len(tables)})")
print("="*100 + "\n")

for idx, (table_name,) in enumerate(tables, 1):
    print(f"\n[{idx}] TABLE: {table_name}")
    print("-" * 100)
    
    # Get column information
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    row_count = cursor.fetchone()[0]
    
    print(f"Rows: {row_count} | Columns: {len(columns)}\n")
    
    print(f"{'Column Name':<40} {'Type':<20} {'Constraints':<30}")
    print(f"{'-'*40} {'-'*20} {'-'*30}")
    
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        constraints = []
        if pk:
            constraints.append("PRIMARY KEY")
        if not_null:
            constraints.append("NOT NULL")
        
        constraints_str = ", ".join(constraints) if constraints else "-"
        print(f"{col_name:<40} {col_type:<20} {constraints_str:<30}")

conn.close()
print("\n" + "="*100 + "\n")
