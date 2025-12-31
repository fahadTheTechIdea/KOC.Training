"""
Authentication Configuration Model
Stores system-wide authentication configuration (admin configurable)
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


class AuthConfig(db.Model):
    """Authentication configuration (single row for system-wide config)"""
    __tablename__ = 'auth_config'
    
    id = db.Column(db.Integer, primary_key=True)
    auth_mode = db.Column(db.String(50), nullable=False, default='local')  # 'local', 'identity_server', 'microsoft_sso'
    
    # Identity Server configuration
    identity_server_url = db.Column(db.String(500))
    identity_server_client_id = db.Column(db.String(200))
    identity_server_client_secret_encrypted = db.Column(db.Text)  # Encrypted
    
    # Microsoft SSO configuration
    microsoft_tenant_id = db.Column(db.String(200))
    microsoft_client_id = db.Column(db.String(200))
    microsoft_client_secret_encrypted = db.Column(db.Text)  # Encrypted
    microsoft_redirect_uri = db.Column(db.String(500))
    
    # JWT configuration
    jwt_secret_key_encrypted = db.Column(db.Text)  # Encrypted
    jwt_token_expires = db.Column(db.Integer, default=3600)  # Seconds
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_identity_server_client_secret(self, secret: str):
        """Set encrypted Identity Server client secret"""
        self.identity_server_client_secret_encrypted = _encrypt_value(secret) if secret else None
    
    def get_identity_server_client_secret(self) -> str:
        """Get decrypted Identity Server client secret"""
        if self.identity_server_client_secret_encrypted:
            return _decrypt_value(self.identity_server_client_secret_encrypted)
        return None
    
    def set_microsoft_client_secret(self, secret: str):
        """Set encrypted Microsoft client secret"""
        self.microsoft_client_secret_encrypted = _encrypt_value(secret) if secret else None
    
    def get_microsoft_client_secret(self) -> str:
        """Get decrypted Microsoft client secret"""
        if self.microsoft_client_secret_encrypted:
            return _decrypt_value(self.microsoft_client_secret_encrypted)
        return None
    
    def set_jwt_secret_key(self, secret: str):
        """Set encrypted JWT secret key"""
        self.jwt_secret_key_encrypted = _encrypt_value(secret) if secret else None
    
    def get_jwt_secret_key(self) -> str:
        """Get decrypted JWT secret key"""
        if self.jwt_secret_key_encrypted:
            return _decrypt_value(self.jwt_secret_key_encrypted)
        return None
    
    def to_dict(self, include_secrets: bool = False):
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'auth_mode': self.auth_mode,
            'identity_server_url': self.identity_server_url,
            'identity_server_client_id': self.identity_server_client_id,
            'microsoft_tenant_id': self.microsoft_tenant_id,
            'microsoft_client_id': self.microsoft_client_id,
            'microsoft_redirect_uri': self.microsoft_redirect_uri,
            'jwt_token_expires': self.jwt_token_expires,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_secrets:
            result['identity_server_client_secret'] = self.get_identity_server_client_secret()
            result['microsoft_client_secret'] = self.get_microsoft_client_secret()
            result['jwt_secret_key'] = self.get_jwt_secret_key()
        return result
    
    @staticmethod
    def get_config():
        """Get current authentication configuration (singleton pattern)"""
        config = AuthConfig.query.first()
        if not config:
            # Create default config
            config = AuthConfig(auth_mode='local')
            db.session.add(config)
            db.session.commit()
        return config
    
    def __repr__(self):
        return f'<AuthConfig mode={self.auth_mode}>'
