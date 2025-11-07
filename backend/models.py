# backend/models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    branch = Column(String(255))
    whatsapp = Column(String(255), unique=True, index=True)
    personal_code = Column(String(255), unique=True, index=True)
    
    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="client")  # superadmin, warehouse_admin, client
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Warehouse assignment (for warehouse_admin role)
    assigned_warehouse = Column(String(255), nullable=True)  # "РљРёС‚Р°Р№", "РђР»РјР°С‚С‹", "РЁС‹РјРєРµРЅС‚" etc


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)  # <- уникальный столбец
    address = Column(String)
    phone = Column(String)
    manager_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)




class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True)
    track_number = Column(String, unique=True, index=True)
    personal_code = Column(String, index=True)
    notes = Column(Text)
    current_status = Column(String, default="Ожидание обновления")
    
    china_arrival = Column(DateTime)
    china_departure = Column(DateTime)
    kz_arrival = Column(DateTime)
    handout_date = Column(DateTime)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class WarehouseTransfer(Base):
    __tablename__ = "warehouse_transfers"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    track_number = Column(String(255), ForeignKey('tracks.track_number'), nullable=False)
    from_warehouse = Column(String(255), nullable=False)
    to_warehouse = Column(String(255), nullable=False)
    transfer_date = Column(DateTime, default=datetime.utcnow)
    transferred_by = Column(String(255), nullable=True)  # Admin email
    note = Column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255), nullable=False)
    performed_by = Column(String(255), nullable=False)
    target_entity = Column(String(100), nullable=True)
    target_id = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)