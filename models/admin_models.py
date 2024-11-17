# models/admin_models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from extensions import db


roles_permissions = db.Table(
    'roles_permissions',
    db.metadata,  # Use the same metadata instance
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
    extend_existing=True  # Allow extending existing table
)

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_user'
    __table_args__ = {'extend_existing': True}  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = relationship('Role', back_populates='users')

    def has_permission(self, permission_name):
        if self.role and self.role.has_permission(permission_name):
            return True
        return False

    def is_superadmin(self):
        return self.role and self.role.name == 'SuperAdmin'

class Role(db.Model):
    __tablename__ = 'role'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    permissions = relationship('Permission', secondary=roles_permissions, back_populates='roles')
    users = relationship('AdminUser', back_populates='role')

    def has_permission(self, permission_name):
        return any(permission.name == permission_name for permission in self.permissions)

class Permission(db.Model):
    __tablename__ = 'permission'
    __table_args__ = {'extend_existing': True} 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    roles = relationship('Role', secondary=roles_permissions, back_populates='permissions')
