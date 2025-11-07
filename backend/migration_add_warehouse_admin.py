# migration_add_warehouse_admin.py
"""
Migration script to add warehouse admin functionality
Run this once to update your database structure
"""

from backend.db import SessionLocal, engine
from backend.models import Base, User, Warehouse
from sqlalchemy import text

def run_migration():
    print("="*80)
    print("МИГРАЦИЯ: Добавление поддержки администраторов складов")
    print("="*80)

    db = SessionLocal()

    try:
        # 1. Check if assigned_warehouse column exists in users table
        print("\n1. Проверка колонки assigned_warehouse...")
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('users') 
            WHERE name='assigned_warehouse'
        """)).fetchone()

        if result[0] == 0:
            print("   ✓ Добавляем колонку assigned_warehouse к таблице users...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN assigned_warehouse VARCHAR(255)
            """))
            db.commit()
            print("   ✅ Колонка добавлена")
        else:
            print("   ✓ Колонка assigned_warehouse уже существует")

        # 2. Update existing warehouse_admin users
        print("\n2. Обновление существующих warehouse_admin пользователей...")
        warehouse_admins = db.query(User).filter(User.role == "warehouse_admin").all()

        if warehouse_admins:
            print(f"   Найдено {len(warehouse_admins)} warehouse_admin пользователей")
            for admin in warehouse_admins:
                if not admin.assigned_warehouse:
                    # Try to assign based on branch
                    admin.assigned_warehouse = admin.branch
                    print(f"   ✓ Назначен склад '{admin.branch}' для {admin.email}")
            db.commit()
            print("   ✅ Пользователи обновлены")
        else:
            print("   ℹ️  Нет warehouse_admin пользователей")

        # 3. Create default warehouses if none exist
        print("\n3. Проверка складов...")
        warehouse_count = db.query(Warehouse).count()

        if warehouse_count == 0:
            print("   ℹ️  Создаем склады по умолчанию...")
            default_warehouses = [
                {"name": "Склад Китай", "code": "CN", "address": "Китай"},
                {"name": "Склад Алматы", "code": "ALM", "address": "Алматы"},
                {"name": "Склад Шымкент", "code": "SHM", "address": "Шымкент"},
            ]

            for wh_data in default_warehouses:
                warehouse = Warehouse(**wh_data, is_active=True)
                db.add(warehouse)
                print(f"   ✓ Создан склад: {wh_data['name']}")

            db.commit()
            print("   ✅ Склады созданы")
        else:
            print(f"   ✓ Найдено {warehouse_count} складов")

        # 4. Show summary
        print("\n" + "="*80)
        print("РЕЗУЛЬТАТЫ МИГРАЦИИ:")
        print("="*80)

        total_users = db.query(User).count()
        total_warehouses = db.query(Warehouse).count()
        warehouse_admins = db.query(User).filter(User.role == "warehouse_admin").count()

        print(f"✅ Всего пользователей: {total_users}")
        print(f"✅ Администраторов складов: {warehouse_admins}")
        print(f"✅ Всего складов: {total_warehouses}")

        # List warehouse admins
        if warehouse_admins > 0:
            print("\n📋 Администраторы складов:")
            admins = db.query(User).filter(User.role == "warehouse_admin").all()
            for admin in admins:
                print(f"   • {admin.email} → {admin.assigned_warehouse or 'НЕ НАЗНАЧЕН'}")

        # List warehouses
        if total_warehouses > 0:
            print("\n🏭 Склады:")
            warehouses = db.query(Warehouse).all()
            for wh in warehouses:
                status = "✅ Активен" if wh.is_active else "❌ Неактивен"
                print(f"   • {wh.name} ({wh.code}) - {status}")

        print("\n" + "="*80)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ ОШИБКА МИГРАЦИИ: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
