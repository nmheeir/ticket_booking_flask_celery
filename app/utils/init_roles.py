from app.models.role import Role
from app.utils.permissions import Permission
from app.utils.database import db, commit_changes

def init_roles():
    """Initialize default roles"""
    # Create roles if they don't exist
    roles = {
        'user': {
            'name': 'User',
            'description': 'Regular user with basic permissions',
            'permissions': Permission.USER
        },
        'staff': {
            'name': 'Staff',
            'description': 'Staff member with event management permissions',
            'permissions': Permission.STAFF
        },
        'admin': {
            'name': 'Administrator',
            'description': 'Administrator with full system access',
            'permissions': Permission.ADMIN
        }
    }

    for role_key, role_data in roles.items():
        role = Role.query.filter_by(name=role_data['name']).first()
        if role is None:
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                permissions=role_data['permissions']
            )
            db.session.add(role)
    
    try:
        commit_changes()
        print("Roles initialized successfully")
    except Exception as e:
        print(f"Error initializing roles: {e}")
        db.session.rollback() 