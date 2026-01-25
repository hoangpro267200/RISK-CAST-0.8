#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('riskcast.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables in database:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')
conn.close()
