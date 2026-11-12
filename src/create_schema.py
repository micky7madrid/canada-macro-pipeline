import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=tcp:{os.environ['AZURE_SQL_SERVER']},1433;"
    f"Database={os.environ['AZURE_SQL_DATABASE']};"
    f"Uid={os.environ['AZURE_SQL_USER']};"
    f"Pwd={os.environ['AZURE_SQL_PASSWORD']};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
)

with open("sql/schema.sql") as f:
    script = f.read()

statements = [s.strip() for s in script.split(";") if s.strip()]

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

for stmt in statements:
    cursor.execute(stmt)

conn.commit()

cursor.execute("SELECT name FROM sys.tables ORDER BY name")
print("Tables in the database:")
for row in cursor.fetchall():
    print(" -", row[0])

conn.close()