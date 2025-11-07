# check_db.py
import sqlite3

conn = sqlite3.connect('cargo.db')
cursor = conn.cursor()

# Получить структуру таблицы tracks
cursor.execute("PRAGMA table_info(tracks)")
columns = cursor.fetchall()

print("=== СТРУКТУРА ТАБЛИЦЫ TRACKS ===")
for col in columns:
    print(f"{col[1]} ({col[2]})")  # название и тип колонки

conn.close()
