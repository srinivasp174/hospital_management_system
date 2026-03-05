from models.user import User, UserRole
from extensions import db
from flask import current_app

def create_admin():
    """Creates default admin user
    """
    
    # Check if admin exists
    existing_admin = User.query.filter_by(role=UserRole.ADMIN).first()
    
    if existing_admin:
        current_app.logger.info("Admin already exists")
        return
    
    # Create admin user
    admin = User(
        first_name='Super',
        middle_name=None,
        last_name='Admin',
        phone='9999999999',
        email='admin@hms.com',
        role=UserRole.ADMIN,
        is_active=True
    )
    
    admin.set_password("admin123")
    
    db.session.add(admin)
    db.session.commit()
    
    current_app.logger.info("Default admin created")