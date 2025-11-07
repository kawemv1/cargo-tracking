from sqlalchemy.orm import Session
from backend.models import AuditLog, User
from datetime import datetime
from typing import Optional
import json


class AuditLogger:
    """Centralized audit logging service."""
    
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        performed_by: str,
        target_entity: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log a user action to the audit log.
        
        Args:
            db: Database session
            action: Action performed (e.g., "LOGIN", "CREATE_USER", "DELETE_TRACK")
            performed_by: Email of user who performed the action
            target_entity: Type of entity affected (e.g., "user", "track", "warehouse")
            target_id: ID of the affected entity
            details: Additional details as dictionary
            ip_address: IP address of the user
        """
        try:
            log_entry = AuditLog(
                action=action,
                performed_by=performed_by,
                target_entity=target_entity,
                target_id=str(target_id) if target_id else None,
                details=json.dumps(details, ensure_ascii=False) if details else None,
                ip_address=ip_address,
                timestamp=datetime.utcnow()
            )
            
            db.add(log_entry)
            db.commit()
            
            print(f"[AUDIT] {action} by {performed_by} on {target_entity}:{target_id}")
            
        except Exception as e:
            print(f"[AUDIT] ❌ Error logging action: {e}")
            db.rollback()
    
    @staticmethod
    def log_login(db: Session, user: User, ip_address: str, success: bool = True):
        """Log a login attempt."""
        AuditLogger.log_action(
            db=db,
            action="LOGIN_SUCCESS" if success else "LOGIN_FAILED",
            performed_by=user.email,
            details={
                "user_id": user.id,
                "role": user.role,
                "name": user.name
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_logout(db: Session, user: User, ip_address: str):
        """Log a logout."""
        AuditLogger.log_action(
            db=db,
            action="LOGOUT",
            performed_by=user.email,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_user_created(db: Session, admin: User, new_user: User, ip_address: str):
        """Log user creation."""
        AuditLogger.log_action(
            db=db,
            action="CREATE_USER",
            performed_by=admin.email,
            target_entity="user",
            target_id=new_user.id,
            details={
                "user_email": new_user.email,
                "user_name": new_user.name,
                "user_role": new_user.role,
                "personal_code": new_user.personal_code
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_user_deleted(db: Session, admin: User, deleted_user_id: int, 
                        deleted_user_email: str, ip_address: str):
        """Log user deletion."""
        AuditLogger.log_action(
            db=db,
            action="DELETE_USER",
            performed_by=admin.email,
            target_entity="user",
            target_id=deleted_user_id,
            details={"deleted_email": deleted_user_email},
            ip_address=ip_address
        )
    
    @staticmethod
    def log_tracks_uploaded(db: Session, admin: User, count: int, 
                           filename: str, ip_address: str):
        """Log track upload."""
        AuditLogger.log_action(
            db=db,
            action="UPLOAD_TRACKS",
            performed_by=admin.email,
            target_entity="track",
            details={
                "count": count,
                "filename": filename
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_track_delivered(db: Session, admin: User, track_number: str, 
                           ip_address: str):
        """Log track delivery."""
        AuditLogger.log_action(
            db=db,
            action="DELIVER_TRACK",
            performed_by=admin.email,
            target_entity="track",
            target_id=track_number,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_track_deleted(db: Session, admin: User, track_number: str, 
                         ip_address: str):
        """Log track deletion."""
        AuditLogger.log_action(
            db=db,
            action="DELETE_TRACK",
            performed_by=admin.email,
            target_entity="track",
            target_id=track_number,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_batch_operation(db: Session, admin: User, operation: str, 
                           count: int, ip_address: str):
        """Log batch operations."""
        AuditLogger.log_action(
            db=db,
            action=f"BATCH_{operation.upper()}",
            performed_by=admin.email,
            details={"count": count},
            ip_address=ip_address
        )
    
    @staticmethod
    def log_warehouse_created(db: Session, admin: User, warehouse_name: str, 
                             warehouse_code: str, ip_address: str):
        """Log warehouse creation."""
        AuditLogger.log_action(
            db=db,
            action="CREATE_WAREHOUSE",
            performed_by=admin.email,
            target_entity="warehouse",
            details={
                "name": warehouse_name,
                "code": warehouse_code
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_warehouse_deleted(db: Session, admin: User, warehouse_id: int, 
                             warehouse_name: str, ip_address: str):
        """Log warehouse deletion."""
        AuditLogger.log_action(
            db=db,
            action="DELETE_WAREHOUSE",
            performed_by=admin.email,
            target_entity="warehouse",
            target_id=warehouse_id,
            details={"name": warehouse_name},
            ip_address=ip_address
        )
    
    @staticmethod
    def log_status_update(db: Session, admin: User, track_number: str, 
                         old_status: str, new_status: str, ip_address: str):
        """Log status update."""
        AuditLogger.log_action(
            db=db,
            action="UPDATE_STATUS",
            performed_by=admin.email,
            target_entity="track",
            target_id=track_number,
            details={
                "old_status": old_status,
                "new_status": new_status
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def get_user_actions(db: Session, user_email: str, limit: int = 100):
        """Get recent actions by a specific user."""
        return db.query(AuditLog).filter(
            AuditLog.performed_by == user_email
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_recent_logs(db: Session, limit: int = 100):
        """Get recent audit logs."""
        return db.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_logs_by_action(db: Session, action: str, limit: int = 100):
        """Get logs filtered by action type."""
        return db.query(AuditLog).filter(
            AuditLog.action == action
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def get_logs_by_entity(db: Session, entity: str, entity_id: str, 
                          limit: int = 100):
        """Get logs for a specific entity."""
        return db.query(AuditLog).filter(
            AuditLog.target_entity == entity,
            AuditLog.target_id == entity_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


# Helper function to get client IP
def get_client_ip(request) -> str:
    """Extract client IP address from request."""
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    # Check X-Forwarded-For header (for proxies)
    if hasattr(request, 'headers'):
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
    
    return "unknown"