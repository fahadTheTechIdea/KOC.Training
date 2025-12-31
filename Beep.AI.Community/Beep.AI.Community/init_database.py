"""
Initialize database with default data
"""
from app import create_app, db
from app.database import init_db, reset_db
from app.models.user import User, UserProfile, APIKey
from werkzeug.security import generate_password_hash
import os
import sys

def create_default_admin():
    """Create default admin user"""
    # Delete existing admin user if it exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("⚠️  Found existing admin user - deleting it...")
        # Delete profile first (if exists)
        if admin.profile:
            db.session.delete(admin.profile)
        # Delete API keys
        for api_key in admin.api_keys:
            db.session.delete(api_key)
        # Delete the user
        db.session.delete(admin)
        db.session.commit()
        print("   Existing admin user deleted.")
    
   

def main():
    """Main initialization function"""
    # Check for --no-reset flag (default is to reset)
    no_reset = '--no-reset' in sys.argv or '--keep' in sys.argv
    
    app = create_app()
    
    with app.app_context():
        if no_reset:
            print("Initializing database (keeping existing data)...")
            init_db()
        else:
            print("⚠️  Resetting database (dropping all tables)...")
            reset_db()
        
        print("Creating default admin user...")
        create_default_admin()
        
        print("\n✅ Database initialization complete!")
        print(f"   Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        if not no_reset:
            print("   ⚠️  Database was reset - all previous data was deleted!")

if __name__ == '__main__':
    main()
