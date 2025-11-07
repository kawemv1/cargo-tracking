# backend/crud.py
import random
import string
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime
import json
from backend.models import AuditLog
from backend.auth import get_password_hash


# ==============================
# Helpers
# ==============================

def log_action(
    session: Session,
    action: str,
    performed_by: str,
    target_entity: str = None,
    target_id: int = None,
    details: dict = None,
    ip_address: str = None  # ✅ Необязательный параметр
):
    """Log admin action to audit trail."""
    log = AuditLog(
        action=action,
        performed_by=performed_by,
        target_entity=target_entity,
        target_id=target_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    session.add(log)
    session.commit()
    return log

def get_next_personal_code(db: Session) -> str:
    """Get next sequential personal code."""
    from backend import models
    max_code = db.query(func.max(models.User.personal_code.cast(Integer))).scalar()
    if max_code is None:
        return "1"
    else:
        return str(max_code + 1)

# backend/crud.py - ADD THESE FUNCTIONS

def create_warehouse(db: Session, name: str, code: str, address: str = None, manager_name: str = None, phone: str = None):
    """Create a new warehouse."""
    from backend import models
    warehouse = models.Warehouse(
        name=name,
        code=code.upper(),
        address=address,
        manager_name=manager_name,
        phone=phone
    )
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


def list_warehouses(db: Session, active_only: bool = True):
    """List all warehouses."""
    from backend import models
    query = db.query(models.Warehouse)
    if active_only:
        query = query.filter(models.Warehouse.is_active == True)
    return query.all()


def get_warehouse_by_code(db: Session, code: str):
    """Get warehouse by code."""
    from backend import models
    return db.query(models.Warehouse).filter(models.Warehouse.code == code.upper()).first()


def receive_parcel_to_warehouse(db: Session, track_number: str, warehouse_code: str, received_by: str):
    """Mark parcel as received in warehouse."""
    from backend import models
    track = db.query(models.Track).filter(models.Track.track_number == track_number.upper()).first()
    if not track:
        return None
    
    warehouse = get_warehouse_by_code(db, warehouse_code)
    if not warehouse:
        return None
    
    track.current_warehouse = warehouse.name
    track.status = f"В складе {warehouse.code}"
    track.received_date = datetime.utcnow()
    track.received_by = received_by
    db.commit()
    
    return track


def handout_parcel_to_client(db: Session, track_number: str, handed_by: str):
    """Mark parcel as handed out to client."""
    from backend import models
    track = db.query(models.Track).filter(models.Track.track_number == track_number.upper()).first()
    if not track:
        return None
    
    track.status = "Выдан клиенту"
    track.handout_date = datetime.utcnow()
    track.handed_by = handed_by
    db.commit()
    
    return track


def transfer_parcel(db: Session, track_number: str, from_warehouse: str, to_warehouse: str, transferred_by: str, note: str = None):
    """Transfer parcel between warehouses."""
    from backend import models
    
    track = db.query(models.Track).filter(models.Track.track_number == track_number.upper()).first()
    if not track:
        return None
    
    # Create transfer record
    transfer = models.WarehouseTransfer(
        track_number=track_number.upper(),
        from_warehouse=from_warehouse,
        to_warehouse=to_warehouse,
        transferred_by=transferred_by,
        note=note
    )
    db.add(transfer)
    
    # Update track location
    track.current_warehouse = to_warehouse
    track.status = f"Переезд: {from_warehouse} → {to_warehouse}"
    
    db.commit()
    return transfer


def get_warehouse_inventory(db: Session, warehouse_name: str):
    """Get all parcels in a warehouse."""
    from backend import models
    return db.query(models.Track).filter(
        models.Track.current_warehouse == warehouse_name,
        models.Track.status != "Выдан клиенту"
    ).all()


def get_parcels_by_warehouse_admin(db: Session, warehouse_name: str):
    """Get parcels for warehouse admin."""
    from backend import models
    return db.query(models.Track).filter(
        models.Track.current_warehouse.like(f"%{warehouse_name}%")
    ).all()


# ==============================
# Users (with Authentication)
# ==============================
def create_user(
    db: Session,
    email: str,
    password: str,
    name: str,
    whatsapp: str,
    branch: str,
    personal_code: str = None,
    role: str = "client"
):
    """Create a new user with hashed password."""
    from backend import models
    
    if not personal_code:
        personal_code = get_next_personal_code(db)
    
    hashed_password = get_password_hash(password)
    
    user = models.User(
        email=email,
        hashed_password=hashed_password,
        name=name,
        whatsapp=whatsapp,
        branch=branch,
        personal_code=personal_code,
        role=role,
        is_active=True
    )
    
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        print(f"[DB] Added user: {user.name}, code: {user.personal_code}, role: {user.role}")
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Email, WhatsApp, or personal code already exists.")
    
    return user


def get_user_by_email(db: Session, email: str):
    """Get user by email."""
    from backend import models
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_personal_code(db: Session, personal_code: str):
    """Get user by personal code."""
    from backend import models
    return db.query(models.User).filter(models.User.personal_code == personal_code).first()


def update_last_login(db: Session, user_id: int):
    """Update user's last login timestamp."""
    from backend import models
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.last_login = datetime.utcnow()
        db.commit()


def list_users(db: Session):
    """List all users."""
    from backend import models
    return db.query(models.User).all()


def delete_user(db: Session, user_id: int):
    """Delete a user."""
    from backend import models
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


# ==============================
# Tracks
# ==============================
def get_track_by_number(db: Session, track_number: str):
    """Get track by number."""
    from backend import models
    return db.query(models.Track).filter(models.Track.track_number == track_number).first()


def get_user_tracks_by_code(db: Session, personal_code: str, is_active: bool = False):
    """Get all tracks for a user by personal code."""
    from backend import models
    return db.query(models.Track).filter(
        models.Track.personal_code == personal_code,
        models.Track.is_active == is_active
    ).all()


def create_or_update_track(db: Session, track_number: str, status: str, departure_date: date):
    """Create or update a track (admin function)."""
    from backend import models
    track = get_track_by_number(db, track_number)
    
    if track:
        track.status = status
        Track.china_departure = departure_date
        track.is_active = False  # Unarchive if was archived
        track.updated_at = datetime.utcnow()
        db.commit()
        print(f"[DB] Updated track: {track_number} to status '{status}'")
    else:
        track = models.Track(
            track_number=track_number,
            current_status=status,
            china_departure=departure_date,
            personal_code=None,
            is_active=False
        )
        db.add(track)
        db.commit()
        print(f"[DB] Created new unassigned track: {track_number} with status '{status}'")
    
    return track


def assign_track_to_user(db: Session, track_number: str, personal_code: str):
    """Assign a track to a user."""
    from backend import models
    track = get_track_by_number(db, track_number)
    
    if track:
        if track.personal_code and track.personal_code != personal_code:
            raise ValueError(f"Track {track_number} is already assigned to another client.")
        track.personal_code = personal_code
        track.updated_at = datetime.utcnow()
        db.commit()
        print(f"[DB] Assigned track {track_number} to user {personal_code}")
        return track
    else:
        new_track = models.Track(
            track_number=track_number,
            current_status="Дата регистрации клиентом",
            china_departure=None,
            personal_code=personal_code,
            is_active=False
        )
        db.add(new_track)
        db.commit()
        db.refresh(new_track)
        print(f"[DB] Registered new track {track_number} by user {personal_code}")
        return new_track


def archive_track(db: Session, track_number: str):
    """Archive a track (soft delete)."""
    from backend import models
    track = get_track_by_number(db, track_number)
    if track:
        track.is_active = True
        track.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


# ==============================
# Audit Logs
# ==============================
def create_audit_log(
    db: Session,
    action: str,
    performed_by: str,
    target_entity: str,
    target_id: str,
    details: str = None
):
    """Create an audit log entry."""
    from backend import models
    log = models.AuditLog(
        action=action,
        performed_by=performed_by,
        target_entity=target_entity,
        target_id=target_id,
        details=details
    )
    db.add(log)
    db.commit()
    print(f"[AUDIT] {action} by {performed_by} on {target_entity}:{target_id}")
