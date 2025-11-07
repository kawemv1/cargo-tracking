# backend/main.py
"""
Delta Cargo Admin System - Main Application with Audit Logging
Complete backend with authentication, tracking, and audit logging
"""

# В начале файла main.py
import os
from datetime import datetime, timedelta, date  # ← ВОТ ЭТО
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Form, Depends, UploadFile, File, status, Request
# ... остальные импорты
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_, func
import shutil
import pandas as pd
from io import BytesIO

# Rate limiting imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Local imports
from . import db
from backend.models import Track, User, Warehouse, AuditLog
import backend.crud as crud
import backend.auth as auth
from backend.schemas import UserRegister, UserLogin, Token, UserOut, TrackAssignment
from backend.logger import AuditLogger, get_client_ip

# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================
def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

app = FastAPI(
    title="Delta Cargo Admin System",
    description="Cargo tracking and management system with audit logging",
    version="1.1.0"
)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
FRONTEND_SRC_DIR = os.path.join(FRONTEND_DIR, "src")

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_SRC_DIR), name="static")
app.mount("/src", StaticFiles(directory="frontend/src"), name="src")

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    db.initialize_database()
    db.Base.metadata.create_all(bind=db.engine)
    print("✅ [APP] FastAPI application started successfully")
    print(f"📁 [APP] Static files directory: {FRONTEND_SRC_DIR}")
    print(f"📁 [APP] Frontend directory: {FRONTEND_DIR}")
    print("📋 [APP] Audit logging enabled")

@app.on_event("shutdown")
def shutdown_event():
    """Clean up database connections on shutdown."""
    db.close_database()
    print("🛑 [APP] Application shutdown complete")

# ============================================================================
# HTML PAGE ROUTES
# ============================================================================

@app.get("/")
def index_page():
    """Serve the main index/landing page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/login")
def login_page():
    """Serve the login page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/admin")
def admin_page():
    """Serve the admin panel page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))

@app.get("/superadmin")
def superadmin_page():
    """Serve the superadmin panel page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "superadmin.html"))

@app.get("/audit-logs")
def audit_logs_page():
    """Serve the audit logs page (superadmin only)."""
    return FileResponse(os.path.join(FRONTEND_DIR, "audit-logs.html"))

@app.post("/api/warehouses", status_code=201)
def create_warehouse(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    address: str = Form(None),
    phone: str = Form(None),
    manager: str = Form(None),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """Create a new warehouse (superadmin only)."""
    code = code.strip().upper()
    
    # Check if warehouse with this code already exists
    existing = session.query(Warehouse).filter(Warehouse.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse code already exists")
    
    # Create new warehouse
    wh = Warehouse(
        name=name.strip(),
        code=code,
        address=address.strip() if address else None,
        phone=phone.strip() if phone else None,
        manager_name=manager.strip() if manager else None,
        is_active=True
    )
    
    session.add(wh)
    
    try:
        session.commit()
        
        # Save all values immediately after commit
        wh_id = wh.id
        wh_name = wh.name
        wh_code = wh.code
        wh_address = wh.address
        
        # Log audit (in separate try-catch to not break warehouse creation)
        try:
            AuditLogger.log_warehouse_created(
                db=session,
                admin=current_user,
                warehouse_name=wh_name,
                warehouse_code=wh_code,
                ip_address=get_client_ip(request)
            )
        except Exception as audit_error:
            print(f"⚠️ Audit log failed: {audit_error}")
        
        print(f"✅ [WAREHOUSE] Created: {wh_name} ({wh_code}) id={wh_id}")
        
        return {
            "success": True,
            "id": wh_id,
            "name": wh_name,
            "code": wh_code,
            "address": wh_address
        }
        
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Warehouse code already exists")
        
    except Exception as e:
        session.rollback()
        print(f"❌ [ERROR] Warehouse creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create warehouse")



@app.post("/api/auth/login")
async def login(
    request: Request,
    session: Session = Depends(db.get_db)
):
    """Login endpoint."""
    try:
        form_data = await request.form()
        username = form_data.get('username')
        password = form_data.get('password')
        
        if not username or not password:
            raise HTTPException(400, "Email и пароль обязательны")
        
        print(f"🔹 [LOGIN] Attempting login: {username}")
        
        user = session.query(User).filter(User.email == username).first()
        
        if not user:
            raise HTTPException(401, "Неверный email или пароль")
        
        if not auth.pwd_context.verify(password, user.hashed_password):
            raise HTTPException(401, "Неверный email или пароль")
        
        if not user.is_active:
            raise HTTPException(403, "Аккаунт деактивирован")
        
        user.last_login = datetime.utcnow()
        session.commit()
        
        access_token = auth.create_access_token(data={"sub": user.email})
        
        crud.log_action(
            session=session,
            action="LOGIN_SUCCESS",
            performed_by=user.email,
            details={
                "user_id": user.id,
                "role": user.role,
                "name": user.name
            }
        )
        
        print(f"✅ [LOGIN] Success: {user.email} ({user.role})")
        
        # ✅ ВОЗВРАЩАЕМ ВСЕ НЕОБХОДИМЫЕ ПОЛЯ
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
            "name": user.name,
            "email": user.email,
            "personal_code": user.personal_code,  # ✅ ОБЯЗАТЕЛЬНО!
            "branch": user.branch  # ✅ ОБЯЗАТЕЛЬНО!
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [LOGIN] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Ошибка входа: {str(e)}")





@app.post("/api/tracks/assign")
async def assign_track(
    request: Request,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """Assign track to user."""
    data = await request.json()
    track_number = data.get('track_number', '').strip().upper()
    personal_code = data.get('personal_code', '').strip()
    description = data.get('description', '').strip() or None
    
    print(f"🔹 [ASSIGN] Received: track={track_number}, code={personal_code}, desc={description}")
    
    if not track_number or len(track_number) < 3:
        raise HTTPException(400, "Трек должен быть минимум 3 символа")
    
    if not personal_code:
        raise HTTPException(400, "Personal code обязателен")
    
    # Ищем существующий трек
    track = session.query(Track).filter(Track.track_number == track_number).first()
    
    if track:
        # Обновляем
        track.personal_code = personal_code  # ← КРИТИЧНО!
        if description:
            track.notes = description
        print(f"✅ [ASSIGN] Updated: {track_number} with code={personal_code}")
    else:
        # Создаём новый
        track = Track(
            track_number=track_number,
            personal_code=personal_code,  # ← КРИТИЧНО!
            notes=description,
            current_status="Ожидание обновления",
            is_active=True,
            created_at=datetime.utcnow()
        )
        session.add(track)
        print(f"✅ [ASSIGN] Created: {track_number} with code={personal_code}")
    
    session.commit()
    session.refresh(track)
    
    print(f"✅ [ASSIGN] Saved to DB: track_number={track.track_number}, personal_code={track.personal_code}")
    
    return {"success": True, "message": "Трек добавлен"}


# DELETE warehouse (superadmin)
@app.delete("/api/warehouses/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """Delete warehouse."""
    wh = session.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(404, "Склад не найден")
    
    # Удаляем без проверки
    session.delete(wh)
    session.commit()
    
    print(f"✅ [WAREHOUSE] Deleted: {wh.name} (id={warehouse_id})")
    return {"success": True, "message": "Склад удалён"}

# === WAREHOUSE EDIT ENDPOINT ===
@app.put("/api/warehouses/{warehouse_id}")
def update_warehouse(
    warehouse_id: int,
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    address: str = Form(None),
    phone: str = Form(None),
    manager: str = Form(None),
    is_active: bool = Form(True),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """Update warehouse details (superadmin only)."""
    wh = session.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Check code uniqueness
    code = code.strip().upper()
    existing = session.query(Warehouse).filter(
        Warehouse.code == code,
        Warehouse.id != warehouse_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Code already exists")
    
    # Update fields
    old_values = {
        "name": wh.name,
        "code": wh.code,
        "address": wh.address,
        "phone": wh.phone,
        "manager": wh.manager_name
    }
    
    wh.name = name.strip()
    wh.code = code
    wh.address = address
    wh.phone = phone
    wh.manager_name = manager
    wh.is_active = is_active
    
    session.commit()
    session.refresh(wh)
    
    # Log changes
    AuditLogger.log_action(
        db=session,
        action="UPDATE_WAREHOUSE",
        performed_by=current_user.email,
        target_entity="warehouse",
        target_id=warehouse_id,
        details={"old": old_values, "new": {"name": name, "code": code}},
        ip_address=get_client_ip(request)
    )
    
    return {"success": True, "warehouse": {
        "id": wh.id,
        "name": wh.name,
        "code": wh.code,
        "address": wh.address,
        "phone": wh.phone,
        "manager": wh.manager_name,
        "is_active": wh.is_active
    }}

@app.post("/api/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Upload Excel file with track numbers (admin only)."""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Only Excel files allowed")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validate columns
        required_cols = ['track_number', 'personal_code']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(400, f"Excel must have columns: {required_cols}")
        
        added = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                track_number = str(row['track_number']).strip()
                personal_code = str(row['personal_code']).strip()
                
                if not track_number or track_number == 'nan':
                    continue
                
                # Check if exists
                existing = session.query(Track).filter(Track.track_number == track_number).first()
                if existing:
                    errors.append(f"Row {idx+2}: Track {track_number} already exists")
                    continue
                
                # Create track
                new_track = Track(
                    track_number=track_number,        # ✅
                    personal_code=personal_code,      # ✅
                    current_status="В Китае",
                    created_at=datetime.now()
                )
                
                session.add(new_track)
                added += 1
                
            except Exception as e:
                errors.append(f"Row {idx+2}: {str(e)}")
        
        session.commit()
        
        # ✅ ОБНОВЛЕНО: добавить склад в лог
        crud.log_action(
            session=session,
            action="UPLOAD_TRACKS",
            performed_by=current_user.email,
            details={
                "filename": file.filename,
                "tracks_added": added,
                "errors_count": len(errors),
                "warehouse": current_user.branch,  # ← ДОБАВЛЕНО
                "branch": current_user.branch      # ← ДОБАВЛЕНО
            }
        )
        
        return {
            "success": True,
            "added": added,
            "errors": errors[:10]  # First 10 errors
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error processing file: {str(e)}")
    
@app.post("/api/tracks/{track_number}/handout")
def handout_track(
    track_number: str,
    recipient_name: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Mark track as handed out."""
    
    track = session.query(Track).filter(Track.track_number == track_number).first()
    if not track:
        raise HTTPException(404, "Track not found")
    
    Track.current_status = "Выдан"
    track.handed_out_at = datetime.now()
    track.handed_out_by = current_user.email
    track.recipient_name = recipient_name
    
    session.commit()
    
    # ✅ Логировать выдачу
    crud.log_action(
        session=session,
        action="HANDOUT_TRACK",
        performed_by=current_user.email,
        target_entity="Track",
        target_id=track.id,
        details={
            "track_number": track_number,
            "recipient": recipient_name,
            "warehouse": current_user.branch,
            "branch": current_user.branch
        }
    )
    
    return {"success": True, "message": "Track handed out"}
@app.put("/api/tracks/{track_id}")
def update_track(
    track_id: int,
    status: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Update track status."""
    
    track = session.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(404, "Track not found")
    
    old_status = Track.current_status
    Track.current_status = status
    
    session.commit()
    
    # ✅ Логировать изменение
    crud.log_action(
        session=session,
        action="UPDATE_TRACK",
        performed_by=current_user.email,
        target_entity="Track",
        target_id=track.id,
        details={
            "track_number": track.track_number,
            "old_status": old_status,
            "new_status": status,
            "warehouse": current_user.branch,
            "branch": current_user.branch
        }
    )
    
    return {"success": True, "message": "Track updated"}


# === USERS FILTERING & SEARCH ===
# === USERS FILTERING & SEARCH ===
@app.get("/api/users/filter")
def filter_users(
    search: str = None,
    role: str = None,
    warehouse: str = None,
    sort_by: str = "name",
    order: str = "asc",
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Filter and search users with sorting."""
    from sqlalchemy import or_
    
    query = session.query(User)
    
    # Role filter
    if role and role.strip():
        query = query.filter(User.role == role)
    
    # Warehouse filter - ИСПРАВЛЕНО
    if warehouse and warehouse.strip():
        # Сначала найти склад по коду
        warehouse_obj = session.query(Warehouse).filter(
            or_(
                Warehouse.code == warehouse,
                Warehouse.name.ilike(f"%{warehouse}%")
            )
        ).first()
        
        if warehouse_obj:
            # Фильтровать по названию ИЛИ коду
            query = query.filter(
                or_(
                    User.branch.ilike(f"%{warehouse_obj.name}%"),
                    User.branch.ilike(f"%{warehouse_obj.code}%"),
                    User.assigned_warehouse == warehouse_obj.code
                )
            )
    
    # Sorting
    if sort_by == "name":
        query = query.order_by(User.name.asc() if order == "asc" else User.name.desc())
    elif sort_by == "email":
        query = query.order_by(User.email.asc() if order == "asc" else User.email.desc())
    elif sort_by == "role":
        query = query.order_by(User.role.asc() if order == "asc" else User.role.desc())
    elif sort_by == "created":
        query = query.order_by(User.created_at.asc() if order == "asc" else User.created_at.desc())
    else:
        query = query.order_by(User.name.asc())
    
    users = query.all()
    
    # Search - фильтруем на уровне Python
    if search and search.strip():
        search_lower = search.strip().lower()
        users = [
            u for u in users
            if (u.name and search_lower in u.name.lower()) or
               (u.email and search_lower in u.email.lower()) or
               (u.personal_code and search_lower in str(u.personal_code).lower()) or
               (u.whatsapp and search_lower in u.whatsapp.lower())
        ]
    
    print(f"🔍 Filter: search='{search}', warehouse='{warehouse}', found {len(users)} users")
    
    return [{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "whatsapp": u.whatsapp,
        "branch": u.branch,
        "role": u.role,
        "personal_code": u.personal_code,
        "assigned_warehouse": u.assigned_warehouse,
        "is_active": u.is_active if hasattr(u, 'is_active') else True,
        "created_at": u.created_at.isoformat() if hasattr(u, 'created_at') and u.created_at else None
    } for u in users]



@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    with open("frontend/logs.html", "r", encoding="utf-8") as f:
        return f.read()

# === CHANGE USER ROLE (superadmin only) ===
@app.put("/api/users/{user_id}/role")
def change_user_role(
    user_id: int,
    request: Request,
    new_role: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """Change user role (superadmin only)."""
    user = session.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if new_role not in ['client', 'admin', 'warehouse_admin', 'superadmin']:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    old_role = user.role
    user.role = new_role
    
    session.commit()
    session.refresh(user)
    
    # Log action
    AuditLogger.log_action(
        db=session,
        action="CHANGE_USER_ROLE",
        performed_by=current_user.email,
        target_entity="user",
        target_id=user_id,
        details={
            "user_email": user.email,
            "old_role": old_role,
            "new_role": new_role
        },
        ip_address=get_client_ip(request)
    )
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }


# === WAREHOUSE-SPECIFIC LOGS ===
@app.get("/api/audit/logs")
def get_audit_logs(
    date_from: str = None,
    date_to: str = None,
    action: str = None,
    user: str = None,
    warehouse: str = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """Get audit logs with filters."""
    from datetime import datetime
    from sqlalchemy import or_, and_
    
    query = session.query(AuditLog)
    
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from))
    
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to))
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user:
        query = query.filter(AuditLog.performed_by.ilike(f"%{user}%"))
    
    # ✅ ИСПРАВЛЕНО: Фильтр по складу
    if warehouse:
        # Ищем в details JSON по полям warehouse и branch
        query = query.filter(
            or_(
                AuditLog.details.contains(f'"warehouse": "{warehouse}"'),
                AuditLog.details.contains(f'"branch": "{warehouse}"'),
                AuditLog.details.contains(f'"warehouse":"{warehouse}"'),
                AuditLog.details.contains(f'"branch":"{warehouse}"')
            )
        )
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()
    
    print(f"🔍 Logs query: warehouse={warehouse}, found={len(logs)}")
    
    return [{
        "id": log.id,
        "timestamp": log.timestamp.isoformat(),
        "action": log.action,
        "performed_by": log.performed_by,
        "target_entity": log.target_entity,
        "target_id": log.target_id,
        "details": log.details,
        "ip_address": log.ip_address
    } for log in logs]



# === WAREHOUSE STATISTICS ===
@app.get("/api/warehouses/{warehouse_code}/stats")
def get_warehouse_stats(
    warehouse_code: str,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Get statistics for specific warehouse."""
    wh = session.query(Warehouse).filter(Warehouse.code == warehouse_code.upper()).first()
    
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Count tracks
    total_tracks = session.query(Track).filter(
        Track.current_warehouse.ilike(f'%{warehouse_code}%')
    ).count()
    
    delivered = session.query(Track).filter(
        Track.current_warehouse.ilike(f'%{warehouse_code}%'),
        Track.current_status == "Выдан клиенту"
    ).count()
    
    in_transit = total_tracks - delivered
    
    # Count users
    users_count = session.query(User).filter(
        func.or_(
            User.branch.ilike(f'%{wh.name}%'),
            User.assigned_warehouse == warehouse_code
        )
    ).count()
    
    # Recent activity
    recent_logs = session.query(AuditLog).filter(
        AuditLog.details.ilike(f'%{warehouse_code}%')
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return {
        "warehouse": {
            "id": wh.id,
            "name": wh.name,
            "code": wh.code,
            "address": wh.address,
            "manager": wh.manager_name
        },
        "stats": {
            "total_tracks": total_tracks,
            "delivered": delivered,
            "in_transit": in_transit,
            "users_count": users_count
        },
        "recent_activity": [{
            "action": log.action,
            "by": log.performed_by,
            "time": log.timestamp.isoformat() if log.timestamp else None
        } for log in recent_logs]
    }


# === EXPORT USERS ===
@app.get("/api/users/export")
def export_users(
    format: str = "csv",
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """Export users to CSV/Excel."""
    users = session.query(User).all()
    
    if format == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Email', 'WhatsApp', 'Branch', 'Role', 'Personal Code', 'Assigned Warehouse', 'Created'])
        
        for u in users:
            writer.writerow([
                u.id, u.name, u.email, u.whatsapp, u.branch, u.role, 
                u.personal_code, u.assigned_warehouse, 
                u.created_at.isoformat() if u.created_at else ''
            ])
        
        from fastapi.responses import StreamingResponse
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users.csv"}
        )
    
    return {"error": "Format not supported"}


# === BULK STATUS UPDATE BY WAREHOUSE ===
@app.post("/api/tracks/bulk-update-warehouse")
def bulk_update_by_warehouse(
    request: Request,
    payload: dict,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Update all tracks in a warehouse to new status."""
    warehouse_code = payload.get("warehouse")
    new_status = payload.get("status")
    
    if not warehouse_code or not new_status:
        raise HTTPException(status_code=400, detail="Missing parameters")
    
    tracks = session.query(Track).filter(
        Track.current_warehouse.ilike(f'%{warehouse_code}%')
    ).all()
    
    count = 0
    for track in tracks:
        Track.current_status = new_status
        count += 1
    
    session.commit()
    
    AuditLogger.log_action(
        db=session,
        action="BULK_UPDATE_WAREHOUSE",
        performed_by=current_user.email,
        target_entity="track",
        details={"warehouse": warehouse_code, "status": new_status, "count": count},
        ip_address=get_client_ip(request)
    )
    
    return {"success": True, "updated": count}


# === USER BLOCK/UNBLOCK ===
@app.post("/api/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    request: Request,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Block/Unblock user."""
    user = session.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    session.commit()
    
    action = "BLOCK_USER" if not user.is_active else "UNBLOCK_USER"
    AuditLogger.log_action(
        db=session,
        action=action,
        performed_by=current_user.email,
        target_entity="user",
        target_id=user_id,
        details={"email": user.email},
        ip_address=get_client_ip(request)
    )
    
    return {"success": True, "is_active": user.is_active}


@app.get("/api/warehouses/active")
def get_active_warehouses(
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    warehouses = session.query(Warehouse).filter(Warehouse.is_active == True).order_by(Warehouse.name.asc()).all()
    return [{"id": w.id, "name": w.name, "code": w.code, "address": w.address} for w in warehouses]

@app.post("/api/tracks/upload")
async def upload_tracks(
    request: Request,  # ← ДОБАВЬ ЭТУ СТРОКУ!
    file: UploadFile = File(...),
    departuredate: str = Form(...),
    status: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Upload tracks from Excel/CSV file."""
    # ... остальной код

    """Upload tracks from file with warehouse assignment."""
    if not warehouse:
        raise HTTPException(status_code=400, detail="Warehouse is required")

    wh = session.query(Warehouse).filter(Warehouse.code == warehouse.upper()).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    try:
        contents = await file.read()
        
        # Parse file based on type
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(contents), header=None)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(contents), header=None)
        else:
            # Plain text file
            track_numbers = contents.decode('utf-8').splitlines()
            df = pd.DataFrame(track_numbers)

        track_numbers = df[0].dropna().astype(str).str.strip().str.upper()
        
        count = 0
        for tn in track_numbers:
            if tn and tn != 'NAN':
                track = crud.create_or_update_track(
                    session, tn, status,
                    datetime.strptime(departure_date, '%Y-%m-%d').date()
                )
                track.current_warehouse = f"{wh.name} ({wh.code})"
                count += 1

        session.commit()
        
        AuditLogger.log_tracks_uploaded(
            session, current_user, count, file.filename,
            ip_address=get_client_ip(request)
        )

        return {"success": True, "imported": count, "updated": count}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/api/tracks/batch-update-status")
def batch_update_status(
    request: Request,  # Добавить request
    payload: dict,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Batch update track status by date with optional warehouse."""
    date_str = payload.get("china_departure")
    new_status = payload.get("new_status")
    warehouse_code = payload.get("warehouse")

    if not date_str or not new_status:
        raise HTTPException(status_code=400, detail="departure_date and new_status required")

    targetdate = datetime.strptime(date, '%Y-%m-%d').date()
    tracks = session.query(Track).filter(Track.china_departure == target_date).all()

    wh = None
    if warehouse_code:
        wh = session.query(Warehouse).filter(Warehouse.code == warehouse_code.upper()).first()
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found")

    updated = 0
    for t in tracks:
        t.status = new_status
        if wh:
            t.current_warehouse = f"{wh.name} ({wh.code})"
        updated += 1

    session.commit()
    
    AuditLogger.log_action(
        session, "BATCH_STATUS_UPDATE", current_user.email, "track",
        details={"count": updated, "new_status": new_status, "date": date_str, "warehouse": warehouse_code},
        ip_address=get_client_ip(request)
    )
    
    return {"updated": updated}


# ============================================================================
# AUTHENTICATION ENDPOINTS WITH LOGGING
# ============================================================================


@app.post("/api/auth/login", response_model=Token)
@limiter.limit("5/minute")
def login_user(
    request: Request,
    login_data: UserLogin,
    session: Session = Depends(db.get_db)
):
    """
    Authenticate user and return JWT token.
    Rate limited to 5 attempts per minute per IP.
    """
    user = auth.authenticate_user(session, login_data.email, login_data.password)

    if not user:
        # Log failed login attempt
        AuditLogger.log_action(
            db=session,
            action="LOGIN_FAILED",
            performed_by=login_data.email,
            details={"reason": "Invalid credentials"},
            ip_address=get_client_ip(request)
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Update last login timestamp
    crud.update_last_login(session, user.id)

    # Create JWT token
    access_token = auth.create_user_token(user)

    # Log successful login
    AuditLogger.log_login(
        db=session,
        user=user,
        ip_address=get_client_ip(request),
        success=True
    )

    print(f"✅ [AUTH] User logged in: {user.email} (Role: {user.role})")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "personal_code": user.personal_code,
            "role": user.role,
            "branch": user.branch,
            "whatsapp": user.whatsapp
        }
    }

@app.get("/api/auth/me", response_model=UserOut)
def get_current_user_info(
    current_user: User = Depends(auth.get_current_active_user)
):
    """Get current authenticated user information."""
    return current_user

# ============================================================================
# USER MANAGEMENT ENDPOINTS WITH LOGGING
# ============================================================================

@app.post("/api/users")
def add_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    whatsapp: str = Form(...),
    branch: str = Form(...),
    personal_code: str = Form(None),
    role: str = Form("client"),
    assigned_warehouse: str = Form(None),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Create a new user (admin function)."""
    # Проверки ВНУТРИ функции
    if not branch:
        raise HTTPException(status_code=400, detail="Warehouse (branch) is required")

    if role == "warehouse_admin" and not assigned_warehouse:
        raise HTTPException(status_code=400, detail="assigned_warehouse is required for warehouse_admin")

    try:
        user = crud.create_user(
            session,
            email=email,
            password=password,
            name=name,
            whatsapp=whatsapp,
            branch=branch,
            personal_code=personal_code,
            role=role
        )

        # Assign warehouse if warehouse_admin
        if assigned_warehouse and role == "warehouse_admin":
            user.assigned_warehouse = assigned_warehouse
            session.commit()

        # Log user creation
        AuditLogger.log_user_created(
            db=session,
            admin=current_user,
            new_user=user,
            ip_address=get_client_ip(request)
        )

        print(f"✅ [ADMIN] User created by {current_user.email}: {user.email} (Role: {role})")

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "personal_code": user.personal_code,
            "role": user.role,
            "branch": user.branch,
            "assigned_warehouse": user.assigned_warehouse
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/users")
def get_users(
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Get list of all users.
    Requires admin or superadmin role.
    """
    users = session.query(User).all()

    return [{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "whatsapp": u.whatsapp,
        "branch": u.branch,
        "role": u.role,
        "personal_code": u.personal_code,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]

@app.delete("/api/users/{user_id}")
def delete_user(
    request: Request,
    user_id: int,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Delete a user by ID.
    Requires admin or superadmin role.
    """
    user = session.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "superadmin" and current_user.role != "superadmin":
        raise HTTPException(
            status_code=403,
            detail="Only superadmin can delete superadmin users"
        )

    deleted_email = user.email
    session.delete(user)
    session.commit()

    # Log user deletion
    AuditLogger.log_user_deleted(
        db=session,
        admin=current_user,
        deleted_user_id=user_id,
        deleted_user_email=deleted_email,
        ip_address=get_client_ip(request)
    )

    print(f"✅ [ADMIN] User deleted by {current_user.email}: {deleted_email}")

    return {"success": True, "message": "User deleted successfully"}

# ============================================================================
# TRACK MANAGEMENT ENDPOINTS WITH LOGGING
# ============================================================================

@app.post("/api/tracks")
async def upload_tracks(
    request: Request,
    file: UploadFile = File(...),
    departuredate: str = Form(...),
    status: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Upload tracks from Excel/CSV file."""
    count = 0
    errors = []
    
    try:
        # Parse the date
        departure_dt = datetime.strptime(departuredate, '%Y-%m-%d').date()
        
        # Read file contents
        contents = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            df = pd.read_excel(BytesIO(contents), header=None)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(contents), header=None)
        else:
            # Treat as plain text file
            track_numbers = contents.decode('utf-8').splitlines()
            df = pd.DataFrame(track_numbers)
        
        # Extract track numbers from first column
        track_numbers = df[0].dropna().astype(str).str.strip().str.upper()
        
        # Process each track number
        for track_number in track_numbers:
            if track_number and track_number != 'NAN':
                try:
                    # Check if track already exists
                    existing = session.query(Track).filter(
                        Track.track_number == track_number
                    ).first()
                    
                    if existing:
                        # Update existing track
                        existing.current_status = status
                        existing.china_departure = departure_dt
                    else:
                        # Create new track
                        newtrack = Track(
                            track_number=track_number,
                            current_status=status,
                            china_departure=departure_dt
                        )
                        session.add(newtrack)
                        count += 1
                        
                except Exception as e:
                    errors.append(f"{track_number}: {str(e)}")
        
        session.commit()
        
        # Log tracks upload
        AuditLogger.log_tracks_uploaded(
            db=session,
            admin=current_user,
            count=count,
            filename=file.filename,
            ip_address=get_client_ip(request)
        )
        
        print(f"✅ [TRACKS] Uploaded {count} tracks by {current_user.email}")
        return {"success": True, "count": count, "errors": errors}
        
    except Exception as e:
        session.rollback()
        print(f"❌ [TRACKS] Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/tracks/search/{track_number}")
def search_track(
    track_number: str,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    Search for a specific track by track number.
    Returns track details or 404.
    """
    track = session.query(Track).filter(
        Track.track_number == track_number.upper()
    ).first()

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return {
        "id": track.id,
        "track_number": track.track_number,
        "status": Track.current_status,
        "personal_code": track.personal_code,
        "departuredate": Track.china_departure.isoformat() if Track.china_departure else None,
        "arrivaldate": track.arrival_date.isoformat() if track.arrival_date else None,
        "currentwarehouse": track.current_warehouse
    }

@app.get("/api/users/{user_identifier}/tracks")
def get_user_tracks_simple(user_identifier: str, session: Session = Depends(db.get_db), current_user: User = Depends(auth.get_current_user)):
    try:
        print(f"🔹 Looking for tracks: {user_identifier}")
        tracks = session.query(Track).filter(Track.personal_code == user_identifier).all()
        print(f"✅ Found: {len(tracks)}")
        result = []
        for t in tracks:
            result.append({"track_number": t.track_number, "current_status": t.current_status or "Ожидание", "personal_code": t.personal_code, "is_assigned": True, "status_timeline": [{"status": "Китай", "date": t.china_arrival.strftime('%d.%m.%Y') if t.china_arrival else "—", "completed": bool(t.china_arrival)}, {"status": "Отправлено", "date": t.china_departure.strftime('%d.%m.%Y') if t.china_departure else "—", "completed": bool(t.china_departure)}, {"status": "Склад", "date": t.kz_arrival.strftime('%d.%m.%Y') if t.kz_arrival else "—", "completed": bool(t.kz_arrival)}, {"status": "Выдано", "date": t.handout_date.strftime('%d.%m.%Y') if t.handout_date else "—", "completed": bool(t.handout_date)}]})
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return []



@app.post("/api/tracks/deliver-batch")
def deliver_batch(
    request: Request,
    track_numbers: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Mark multiple tracks as delivered to client."""
    delivered = []
    errors = []

    tracks_list = [t.strip().upper() for t in track_numbers.split(",") if t.strip()]

    for tn in tracks_list:
        # ✅ ИСПРАВЛЕНО: track_number вместо track_number
        track = session.query(Track).filter(Track.track_number == tn).first()
        if track:
            Track.current_status = "Выдан клиенту"
            track.handout_date = datetime.utcnow()
            track.handed_by = current_user.email
            delivered.append(tn)
        else:
            errors.append(tn)

    session.commit()

    # Логирование
    try:
        crud.log_action(
            session=session,
            action="BATCH_DELIVER",
            performed_by=current_user.email,
            details={
                "count": len(delivered),
                "warehouse": current_user.branch,
                "branch": current_user.branch,
                "tracks": delivered[:20],
                "total_tracks": len(delivered),
                "errors": errors[:10],
                "errors_count": len(errors)
            },
            ip_address=get_client_ip(request)
        )
    except Exception as e:
        print(f"⚠️ Failed to log: {e}")

    print(f"✅ [TRACKS] Delivered {len(delivered)} parcels by {current_user.email}")

    return {
        "success": True,
        "delivered": len(delivered),
        "errors": errors
    }


@app.post("/api/tracks/delete-batch")
def delete_batch_tracks(
    request: Request,
    track_numbers: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Delete multiple tracks at once."""
    track_list = [t.strip().upper() for t in track_numbers.split(',') if t.strip()]
    deleted = []

    for track_number in track_list:
        # ✅ ИСПРАВЛЕНО: Track.track_number
        track = session.query(Track).filter(Track.track_number == track_number).first()
        if track:
            session.delete(track)
            deleted.append(track_number)

    session.commit()

    # Логирование
    try:
        crud.log_action(
            session=session,
            action="BATCH_DELETE",
            performed_by=current_user.email,
            details={
                "count": len(deleted),
                "warehouse": current_user.branch,
                "branch": current_user.branch,
                "tracks": deleted[:20],
                "total_tracks": len(deleted)
            },
            ip_address=get_client_ip(request)
        )
    except Exception as e:
        print(f"⚠️ Failed to log: {e}")

    print(f"✅ [TRACKS] Deleted {len(deleted)} tracks by {current_user.email}")

    return {"success": True, "deleted": len(deleted)}

@app.post("/api/auth/register")
async def register(
    request: Request,
    session: Session = Depends(db.get_db)
):
    """Register new user (public endpoint)."""
    
    try:
        # Получаем данные из формы вручную
        form_data = await request.form()
        
        name = form_data.get('name')
        email = form_data.get('email')
        password = form_data.get('password')
        whatsapp = form_data.get('whatsapp')
        branch = form_data.get('branch')
        
        # Валидация
        if not all([name, email, password, whatsapp, branch]):
            raise HTTPException(400, "Все поля обязательны")
        
        print(f"[REGISTER] Attempting registration: {email} at {branch}")
        
        # Проверка существования email
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(400, "Email уже зарегистрирован")
        
        # Проверка существования WhatsApp
        existing_wa = session.query(User).filter(User.whatsapp == whatsapp).first()
        if existing_wa:
            raise HTTPException(400, "WhatsApp уже зарегистрирован")
        
        # Хеширование пароля
        hashed_password = auth.pwd_context.hash(password)
        
        # Создание пользователя
        new_user = User()
        new_user.name = name
        new_user.email = email
        new_user.hashed_password = hashed_password
        new_user.whatsapp = whatsapp
        new_user.branch = branch
        new_user.role = "client"
        new_user.is_active = True
        new_user.personal_code = None
        new_user.assigned_warehouse = None
        new_user.created_at = datetime.utcnow()
        new_user.last_login = None
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        # Логирование
        crud.log_action(
            session=session,
            action="REGISTER",
            performed_by=email,
            details={
                "user_name": name,
                "user_email": email,
                "warehouse": branch,
                "branch": branch
            }
        )
        
        print(f"✅ [REGISTER] New user: {email} at {branch}")
        
        return {
            "success": True,
            "email": email,
            "message": "Регистрация успешна"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [REGISTER] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise HTTPException(500, f"Ошибка регистрации: {str(e)}")


# ============================================================================
# CALENDAR & BATCH UPDATE ENDPOINTS
# ============================================================================

@app.get("/api/tracks/calendar-events")
def calendar_events(
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Get track counts grouped by departure date for calendar display.
    Returns events formatted for FullCalendar.
    """
    results = session.query(
        Track.china_departure,
        func.count(Track.id).label("count")
    ).filter(
        Track.china_departure.isnot(None)
    ).group_by(Track.china_departure).all()

    events = []
    for departure_date, count in results:
        events.append({
            "title": f"{count} посылок",
            "start": departure_date.isoformat(),
            "count": count,
            "backgroundColor": "#667eea",
            "borderColor": "#667eea"
        })

    return events

@app.get("/api/tracks/by-date/{date}")
def get_tracks_by_date(
    date: str,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Get all tracks for a specific departure date.
    Date format: YYYY-MM-DD
    """
    try:
        targetdate = datetime.strptime(date, '%Y-%m-%d').date()
        tracks = session.query(Track).filter(
            Track.china_departure == target_date
        ).all()

        return [{
            "id": t.id,
            "track_number": t.track_number,
            "status": t.status,
            "personal_code": t.personal_code
        } for t in tracks]

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

@app.post("/api/tracks/batch-update")
def batch_update_tracks(
    request: Request,
    date: str = Form(...),
    newstatus: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Update status for all tracks on a specific date.
    Frontend sends: date, newstatus
    """
    try:
        targetdate = datetime.strptime(date, '%Y-%m-%d').date()

        tracks = session.query(Track).filter(
            Track.china_departure == target_date
        ).all()

        count = 0
        for track in tracks:
            Track.current_status = newstatus
            count += 1

        session.commit()

        # Log batch status update
        AuditLogger.log_action(
            db=session,
            action="BATCH_STATUS_UPDATE",
            performed_by=current_user.email,
            target_entity="track",
            details={"count": count, "new_status": newstatus, "date": date},
            ip_address=get_client_ip(request)
        )

        print(f"✅ [TRACKS] Batch updated {count} tracks to '{newstatus}' by {current_user.email}")

        return {
            "success": True,
            "updated": count,
            "message": f"Updated {count} tracks to status: {newstatus}"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WAREHOUSE ENDPOINTS WITH LOGGING
# ============================================================================

@app.get("/api/warehouses")
def list_warehouses(
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Get list of all warehouses."""
    warehouses = crud.list_warehouses(session)

    return [{
        "id": w.id,
        "name": w.name,
        "code": w.code,
        "address": w.address,
        "phone": w.phone,
        "manager": w.manager_name,
        "is_active": w.is_active
    } for w in warehouses]

@app.post("/api/warehouses")
def create_warehouse(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    address: str = Form(None),
    phone: str = Form(None),
    manager: str = Form(None),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """Create a new warehouse (superadmin only)."""
    try:
        warehouse = crud.create_warehouse(
            session,
            name=name,
            code=code,
            address=address,
            phone=phone,
            manager_name=manager
        )

        # Log warehouse creation
        AuditLogger.log_warehouse_created(
            db=session,
            admin=current_user,
            warehouse_name=name,
            warehouse_code=code,
            ip_address=get_client_ip(request)
        )

        return {
            "success": True,
            "warehouse": {
                "id": warehouse.id,
                "name": warehouse.name,
                "code": warehouse.code
            }
        }
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Warehouse code already exists")

# ============================================================================
# AUDIT LOG ENDPOINTS (NEW)
# ============================================================================

@app.get("/api/audit/logs")
def get_audit_logs(
    limit: int = 100,
    action: Optional[str] = None,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """
    Get audit logs (superadmin only).
    Optional filter by action type.
    """
    if action:
        logs = AuditLogger.get_logs_by_action(session, action, limit)
    else:
        logs = AuditLogger.get_recent_logs(session, limit)

    return [{
        "id": log.id,
        "action": log.action,
        "performed_by": log.performed_by,
        "target_entity": log.target_entity,
        "target_id": log.target_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None
    } for log in logs]

@app.get("/api/audit/logs/user/{email}")
def get_user_audit_logs(
    email: str,
    limit: int = 100,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Get audit logs for a specific user.
    Admin can view, but only their own unless superadmin.
    """
    if current_user.role != "superadmin" and current_user.email != email:
        raise HTTPException(
            status_code=403,
            detail="Can only view your own logs"
        )

    logs = AuditLogger.get_user_actions(session, email, limit)

    return [{
        "id": log.id,
        "action": log.action,
        "target_entity": log.target_entity,
        "target_id": log.target_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None
    } for log in logs]

@app.get("/api/audit/logs/entity/{entity}/{entity_id}")
def get_entity_audit_logs(
    entity: str,
    entity_id: str,
    limit: int = 100,
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Get audit logs for a specific entity (track, user, warehouse).
    """
    logs = AuditLogger.get_logs_by_entity(session, entity, entity_id, limit)

    return [{
        "id": log.id,
        "action": log.action,
        "performed_by": log.performed_by,
        "details": log.details,
        "ip_address": log.ip_address,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None
    } for log in logs]

@app.get("/api/audit/stats")
def get_audit_stats(
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """
    Get audit statistics (superadmin only).
    """
    total_logs = session.query(func.count(AuditLog.id)).scalar()

    # Actions by type
    action_counts = session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).all()

    # Most active users
    user_counts = session.query(
        AuditLog.performed_by,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.performed_by).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()

    return {
        "total_logs": total_logs,
        "actions": [{"action": a, "count": c} for a, c in action_counts],
        "most_active_users": [{"email": u, "actions": c} for u, c in user_counts]
    }

# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@app.get("/api/stats")
def get_statistics(
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """Get system statistics (admin only)."""
    total_users = session.query(func.count(User.id)).scalar()
    total_tracks = session.query(func.count(Track.id)).scalar()
    delivered_tracks = session.query(func.count(Track.id)).filter(
        Track.current_status == "Выдан клиенту"
    ).scalar()
    total_warehouses = session.query(func.count(Warehouse.id)).scalar()

    return {
        "total_users": total_users,
        "total_tracks": total_tracks,
        "delivered_tracks": delivered_tracks,
        "in_transit": total_tracks - delivered_tracks,
        "total_warehouses": total_warehouses
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Delta Cargo Admin API",
        "version": "1.1.0"
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler - returns proper JSONResponse."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found", "status_code": 404}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler - returns proper JSONResponse."""
    print(f"❌ [ERROR] Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )
# ============================================================================
# END OF FILE
# ============================================================================
@app.get("/track-history")
def track_history_page():
    """Serve the track history page (admin and superadmin)."""
    return FileResponse(os.path.join(FRONTEND_DIR, "track-history.html"))


# Add this API endpoint to get all tracks
@app.get("/api/tracks/all")
def get_all_tracks(
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_admin)
):
    """
    Get all tracks with full details (admin and superadmin only).
    Returns all tracks ordered by creation date descending.
    """
    from backend.models import Track

    tracks = session.query(Track).order_by(Track.created_at.desc()).all()

    return [{
        "id": t.id,
        "track_number": t.track_number,
        "status": t.status,
        "personal_code": t.personal_code,
        "china_departure": t.china_departure.isoformat() if t.china_departure else None,
        "arrival_date": t.arrival_date.isoformat() if t.arrival_date else None,
        "current_warehouse": t.current_warehouse,
        "handout_date": t.handout_date.isoformat() if t.handout_date else None,
        "handed_by": t.handed_by,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in tracks]
@app.get("/api/warehouses/active")
def get_active_warehouses(
    session: Session = Depends(db.get_db)
    # ❌ УБРАЛИ: current_user: User = Depends(auth.require_admin)
):
    """Get all active warehouses (public endpoint for registration)."""
    warehouses = session.query(Warehouse).filter(Warehouse.is_active == True).all()
    
    return [{
        "id": wh.id,
        "name": wh.name,
        "code": wh.code,
        "address": wh.address,
        "phone": wh.phone,
        "manager_name": wh.manager_name,
        "is_active": wh.is_active
    } for wh in warehouses]
@app.get("/api/public/warehouses")
def get_public_warehouses(session: Session = Depends(db.get_db)):
    """Get active warehouses for registration (public endpoint, no auth required)."""
    warehouses = session.query(Warehouse).filter(Warehouse.is_active == True).all()
    
    print(f"📦 Public warehouses request: found {len(warehouses)} warehouses")
    
    return [{
        "id": wh.id,
        "name": wh.name,
        "code": wh.code
    } for wh in warehouses]

# Assign warehouse to warehouse_admin
@app.post("/api/users/{user_id}/assign-warehouse")
def assign_warehouse_to_admin(
    user_id: int,
    warehouse_code: str = Form(...),
    session: Session = Depends(db.get_db),
    current_user: User = Depends(auth.require_superadmin)
):
    """
    Assign warehouse to warehouse_admin user (superadmin only).
    """
    user = session.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "warehouse_admin":
        raise HTTPException(
            status_code=400, 
            detail="Can only assign warehouse to warehouse_admin users"
        )

    user.assigned_warehouse = warehouse_code
    session.commit()

    print(f"✅ [ADMIN] Assigned warehouse '{warehouse_code}' to {user.email}")

    return {
        "success": True,
        "user_id": user.id,
        "email": user.email,
        "assigned_warehouse": user.assigned_warehouse
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
