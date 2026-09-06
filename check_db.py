import sqlite3
conn = sqlite3.connect('interfaz/database/fraude_yape.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tablas:", tables)
for t in tables:
    name = t[0]
    c.execute(f"SELECT COUNT(*) FROM {name}")
    print(f"  {name}: {c.fetchone()[0]} registros")
    c.execute(f"PRAGMA table_info({name})")
    cols = [row[1] for row in c.fetchall()]
    print(f"  Columnas: {cols}")
conn.close()
