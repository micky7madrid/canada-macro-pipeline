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

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
cursor.execute("SELECT @@VERSION")
print(cursor.fetchone()[0])
conn.close()