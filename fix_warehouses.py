# fix_warehouses.py
import sqlite3
import os

# Проверяем путь к БД
db_path = 'cargo.db'
if not os.path.exists(db_path):
    print(f"❌ БД не найдена: {db_path}")
    print(f"📁 Текущая директория: {os.getcwd()}")
    exit(1)

conn = sqlite3.connect(db_path, isolation_level=None)
conn.execute('PRAGMA encoding = "UTF-8"')
cursor = conn.cursor()

# Проверяем таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"📋 Таблицы в БД: {tables}")

# Находим таблицу складов
warehouse_table = None
for t in tables:
    if 'warehouse' in t.lower():
        warehouse_table = t
        print(f"✅ Найдена таблица: {warehouse_table}")
        break

if not warehouse_table:
    print("❌ Таблица складов не найдена!")
    exit(1)

# Обновляем склады
warehouses = [
    ('Склад в Китае', 'Guangzhou, Baiyun District, China', '+86 20 8888 8888', 'Wang Li', 'CHINA'),
    ('Склад в Алматы', 'г. Алматы, ул. Рыскулова 103', '+7 727 250 5050', 'Айдар Сейтов', 'ALMATY'),
    ('Склад в Шымкенте', 'г. Шымкент, мкр. Нурсат, ул. Байтурсынова 45', '+7 725 256 7070', 'Ерлан Абдрахманов', 'SHYMKENT'),
    ('Склад в Астане', 'г. Астана, район Есиль, пр. Мангилик Ел 55/20', '+7 717 272 8080', 'Асель Нурланова', 'ASTANA'),
]

for name, address, phone, manager, code in warehouses:
    cursor.execute(f"""
        UPDATE {warehouse_table}
        SET name=?, address=?, phone=?, manager_name=? 
        WHERE code=?
    """, (name, address, phone, manager, code))
    print(f"✅ Обновлён: {name}")

conn.close()
print("\n🎉 Склады успешно обновлены!")
