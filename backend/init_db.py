# backend/init_db.py
"""
Initialize database with default admin user.
Run this script to create tables and add first admin.
"""

# backend/init_db.py - REPLACE WITH THIS

if __name__ == "__main__":
    from backend import db, models, crud
    
    print("[INIT] Initializing database...")
    db.initialize_database()
    
    session = db.SessionLocal()
    
    try:
        # Create default warehouses
        warehouses = [
            {"name": "РЎРєР»Р°Рґ РІ РљРёС‚Р°Рµ", "code": "CHINA", "address": "Guangzhou, China"},
            {"name": "РЎРєР»Р°Рґ РІ РђР»РјР°С‚С‹", "code": "ALMATY", "address": "Рі. РђР»РјР°С‚С‹"},
            {"name": "РЎРєР»Р°Рґ РІ РЁС‹РјРєРµРЅС‚Рµ", "code": "SHYMKENT", "address": "Рі. РЁС‹РјРєРµРЅС‚"},
            {"name": "РЎРєР»Р°Рґ РІ РђСЃС‚Р°РЅРµ", "code": "ASTANA", "address": "Рі. РђСЃС‚Р°РЅР°"}
        ]
        
        for wh_data in warehouses:
            existing = session.query(models.Warehouse).filter(
                models.Warehouse.code == wh_data["code"]
            ).first()
            
            if not existing:
                warehouse = models.Warehouse(**wh_data)
                session.add(warehouse)
                print(f"[INIT] Created warehouse: {wh_data['name']}")
        
        session.commit()
        
        # Create superadmin
        existing_super = session.query(models.User).filter(
            models.User.email == "superadmin@deltacargo.com"
        ).first()
        
        if not existing_super:
            print("[INIT] Creating superadmin...")
            superadmin = crud.create_user(
                db=session,
                email="superadmin@deltacargo.com",
                password="super123",
                name="Super Administrator",
                whatsapp="+77000000000",
                branch="HQ",
                personal_code="SUPER001",
                role="superadmin"
            )
            print(f"[INIT] вњ… Superadmin: superadmin@deltacargo.com / super123")
        
        # Create warehouse admin for Almaty
        existing_wh_admin = session.query(models.User).filter(
            models.User.email == "almaty@deltacargo.com"
        ).first()
        
        if not existing_wh_admin:
            print("[INIT] Creating warehouse admin...")
            wh_admin = crud.create_user(
                db=session,
                email="almaty@deltacargo.com",
                password="almaty123",
                name="Almaty Warehouse Admin",
                whatsapp="+77771111111",
                branch="РђР»РјР°С‚С‹",
                role="warehouse_admin"
            )
            wh_admin.assigned_warehouse = "РЎРєР»Р°Рґ РІ РђР»РјР°С‚С‹"
            session.commit()
            print(f"[INIT] вњ… Warehouse Admin: almaty@deltacargo.com / almaty123")
        
        # Create admin (original admin)
        existing_admin = session.query(models.User).filter(
            models.User.email == "admin@deltacargo.com"
        ).first()
        
        if not existing_admin:
            print("[INIT] Creating admin...")
            admin = crud.create_user(
                db=session,
                email="admin@deltacargo.com",
                password="admin123",
                name="Admin User",
                whatsapp="+77771234567",
                branch="HQ",
                personal_code="ADMIN001",
                role="admin"
            )
            print(f"[INIT] вњ… Admin: admin@deltacargo.com / admin123")
        
        # Create test client
        test_client = session.query(models.User).filter(
            models.User.email == "client@test.com"
        ).first()
        
        if not test_client:
            print("[INIT] Creating test client...")
            crud.create_user(
                db=session,
                email="client@test.com",
                password="test123",
                name="Test Client",
                whatsapp="+77757777777",
                branch="Almaty",
                personal_code="TEST001",
                role="client"
            )
            print("[INIT] вњ… Test client: client@test.com / test123")
        
        print("[INIT] рџЋ‰ Database initialization complete!")
        print("\n[INIT] Login credentials:")
        print("  Superadmin: superadmin@deltacargo.com / super123")
        print("  Warehouse Admin: almaty@deltacargo.com / almaty123")
        print("  Admin: admin@deltacargo.com / admin123")
        print("  Client: client@test.com / test123")
        
    except Exception as e:
        print(f"[INIT] вќЊ Error: {e}")
        session.rollback()
    finally:
        session.close()