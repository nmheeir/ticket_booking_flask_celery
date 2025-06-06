from app.utils.database import db

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Integer, default=0)  # Using bitmask for permissions

    # Relationships
    users = db.relationship('User', backref='role', lazy=True)

    def __init__(self, name, description=None, permissions=0):
        self.name = name
        self.description = description
        self.permissions = permissions

    def has_permission(self, permission):
        return self.permissions & permission == permission

    def add_permission(self, permission):
        if not self.has_permission(permission):
            self.permissions += permission

    def remove_permission(self, permission):
        if self.has_permission(permission):
            self.permissions -= permission

    def reset_permissions(self):
        self.permissions = 0

    def __repr__(self):
        return f'<Role {self.name}>' 