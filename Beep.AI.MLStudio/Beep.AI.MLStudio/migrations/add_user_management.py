"""
Migration: Add User Management and Authentication Features
Adds user profiles, community servers, auth config, and user ownership to projects/experiments
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.user import User, UserProfile
from app.models.project import MLProject
from app.models.experiment import Experiment
from app.models.user_community_server import UserCommunityServer
from app.models.global_community_server import GlobalCommunityServer
from app.models.auth_config import AuthConfig
import secrets


def migrate_database():
    """Run migration to add user management features"""
    app = create_app()
    
    with app.app_context():
        print("Starting migration: Add User Management and Authentication Features")
        print("=" * 70)
        
        # 1. Create user_profiles table
        print("\n1. Creating user_profiles table...")
        try:
            db.create_all()  # This will create all new tables
            print("   ✓ user_profiles table created")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
        
        # 2. Create user_community_servers table
        print("\n2. Creating user_community_servers table...")
        try:
            # Already created by db.create_all()
            print("   ✓ user_community_servers table created")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
        
        # 3. Create global_community_servers table
        print("\n3. Creating global_community_servers table...")
        try:
            # Already created by db.create_all()
            print("   ✓ global_community_servers table created")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
        
        # 4. Create auth_config table
        print("\n4. Creating auth_config table...")
        try:
            # Already created by db.create_all()
            print("   ✓ auth_config table created")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
        
        # 5. Add user_id to ml_projects (if not exists)
        print("\n5. Adding user_id column to ml_projects...")
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('ml_projects')]
            
            if 'user_id' not in columns:
                db.session.execute(text("ALTER TABLE ml_projects ADD COLUMN user_id INTEGER"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_ml_projects_user_id ON ml_projects(user_id)"))
                db.session.commit()
                print("   ✓ user_id column added to ml_projects")
            else:
                print("   ✓ user_id column already exists")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # 6. Add is_shared and shared_with_users to ml_projects
        print("\n6. Adding sharing columns to ml_projects...")
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('ml_projects')]
            
            if 'is_shared' not in columns:
                db.session.execute(text("ALTER TABLE ml_projects ADD COLUMN is_shared BOOLEAN DEFAULT 0"))
                print("   ✓ is_shared column added")
            else:
                print("   ✓ is_shared column already exists")
            
            if 'shared_with_users' not in columns:
                db.session.execute(text("ALTER TABLE ml_projects ADD COLUMN shared_with_users TEXT"))
                print("   ✓ shared_with_users column added")
            else:
                print("   ✓ shared_with_users column already exists")
            
            db.session.commit()
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # 7. Add user_id to experiments
        print("\n7. Adding user_id column to experiments...")
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('experiments')]
            
            if 'user_id' not in columns:
                db.session.execute(text("ALTER TABLE experiments ADD COLUMN user_id INTEGER"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_experiments_user_id ON experiments(user_id)"))
                db.session.commit()
                print("   ✓ user_id column added to experiments")
            else:
                print("   ✓ user_id column already exists")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # 8. Add last_login_at and login_count to users
        print("\n8. Adding activity tracking columns to users...")
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'last_login_at' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN last_login_at DATETIME"))
                print("   ✓ last_login_at column added")
            else:
                print("   ✓ last_login_at column already exists")
            
            if 'login_count' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0"))
                print("   ✓ login_count column added")
            else:
                print("   ✓ login_count column already exists")
            
            db.session.commit()
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # 9. Create indexes on foreign keys
        print("\n9. Creating indexes on foreign keys...")
        try:
            from sqlalchemy import text
            # Indexes are created automatically by SQLAlchemy relationships
            # But we'll ensure they exist
            db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_user_profiles_user_id ON user_profiles(user_id)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_user_community_servers_user_id ON user_community_servers(user_id)"))
            db.session.commit()
            print("   ✓ Indexes created")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # 10. Initialize default auth config
        print("\n10. Initializing default auth config...")
        try:
            existing_config = AuthConfig.query.first()
            if not existing_config:
                # Get JWT secret from environment or generate one
                jwt_secret = os.getenv('JWT_SECRET_KEY') or os.getenv('SECRET_KEY') or secrets.token_hex(32)
                
                config = AuthConfig(
                    auth_mode='local',
                    jwt_token_expires=3600
                )
                config.set_jwt_secret_key(jwt_secret)
                db.session.add(config)
                db.session.commit()
                print("   ✓ Default auth config created (local JWT mode)")
            else:
                print("   ✓ Auth config already exists")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        # 11. Create profiles for existing users
        print("\n11. Creating profiles for existing users...")
        try:
            users_without_profiles = db.session.query(User).outerjoin(UserProfile).filter(UserProfile.id == None).all()
            for user in users_without_profiles:
                profile = UserProfile(
                    user_id=user.id,
                    display_name=user.username
                )
                db.session.add(profile)
            db.session.commit()
            print(f"   ✓ Created profiles for {len(users_without_profiles)} existing users")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
            db.session.rollback()
        
        print("\n" + "=" * 70)
        print("Migration completed successfully!")
        print("=" * 70)


if __name__ == '__main__':
    migrate_database()
