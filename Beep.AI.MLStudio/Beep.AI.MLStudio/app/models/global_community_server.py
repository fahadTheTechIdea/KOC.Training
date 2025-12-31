"""
Global Community Server Model
Stores admin-configured global community server connections (accessible to all users)
"""
from datetime import datetime
from app import db
from cryptography.fernet import Fernet
import os
import base64


def _get_encryption_key():
    """Get encryption key from environment or generate one"""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        # Generate a key (in production, this should be set in environment)
        key = Fernet.generate_key().decode()
    else:
        # Ensure it's bytes
        if isinstance(key, str):
            key = key.encode()
    return key


def _encrypt_value(value: str) -> str:
    """Encrypt a value"""
    if not value:
        return None
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception:
        # Fallback: return as-is if encryption fails
        return value


def _decrypt_value(encrypted_value: str) -> str:
    """Decrypt a value"""
    if not encrypted_value:
        return None
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = f.decrypt(decoded)
        return decrypted.decode()
    except Exception:
        # Fallback: return as-is if decryption fails
        return encrypted_value


class GlobalCommunityServer(db.Model):
    """Global community server connection (admin-configured, accessible to all users)"""
    __tablename__ = 'global_community_servers'
    
    id = db.Column(db.Integer, primary_key=True)
    server_name = db.Column(db.String(200), nullable=False)
    server_url = db.Column(db.String(500), nullable=False)
    api_key_encrypted = db.Column(db.Text)  # Encrypted API key
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin user who created it
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def set_api_key(self, api_key: str):
        """Set encrypted API key"""
        self.api_key_encrypted = _encrypt_value(api_key) if api_key else None
    
    def get_api_key(self) -> str:
        """Get decrypted API key"""
        if self.api_key_encrypted:
            return _decrypt_value(self.api_key_encrypted)
        return None
    
    def to_dict(self, include_api_key: bool = False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'server_name': self.server_name,
            'server_url': self.server_url,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_api_key:
            result['api_key'] = self.get_api_key()
        else:
            # Mask API key
            api_key = self.get_api_key()
            if api_key:
                result['api_key'] = api_key[:10] + '...' if len(api_key) > 10 else '***'
        return result
    
    def __repr__(self):
        return f'<GlobalCommunityServer {self.server_name}>'
