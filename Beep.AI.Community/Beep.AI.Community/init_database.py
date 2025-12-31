"""
Initialize database with default data
"""
from app import create_app, db
from app.database import init_db
from app.models.user import User, UserProfile, APIKey
from werkzeug.security import generate_password_hash
import os

def create_default_admin():
    """Create default admin user"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@beep.ai',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        
        profile = UserProfile(
            user_id=admin.id,
            display_name='Admin',
            bio='Platform Administrator'
        )
        db.session.add(profile)
        
        db.session.commit()
        print("Default admin user created: admin / admin123")
        print("⚠️  IMPORTANT: Change the admin password immediately!")

def main():
    """Main initialization function"""
    app = create_app()
    
    with app.app_context():
        print("Initializing database...")
        init_db()
        
        print("Creating default admin user...")
        create_default_admin()
        
        print("\n✅ Database initialization complete!")
        print(f"   Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

if __name__ == '__main__':
    main()
