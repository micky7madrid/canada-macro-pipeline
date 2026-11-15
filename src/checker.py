from load_data import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT name FROM sys.tables ORDER BY name")
for row in cursor.fetchall():
    cursor.execute(f"SELECT COUNT(*) FROM {row[0]}")
    print(row[0], "->", cursor.fetchone()[0], "rows")

conn.close()