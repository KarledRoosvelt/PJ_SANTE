import os
import psycopg2
from pathlib import Path

db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise RuntimeError("DATABASE_URL non défini")

conn = psycopg2.connect(db_url, sslmode="require")
conn.autocommit = True
cur = conn.cursor()

sql_file = Path("scripts/create_tables.sql").resolve()

with open(sql_file, "r", encoding="utf-8") as f:
    sql_script = f.read()

cur.execute(sql_script)

cur.close()
conn.close()

print("✅ Tables créées avec succès dans Render")