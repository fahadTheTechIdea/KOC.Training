"""
Migration: Migrate Existing Projects/Experiments to Default User
Assigns existing projects and experiments without user_id to a default admin user
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.user import User
from app.models.project import MLProject
from app.models.experiment import Experiment
from app.services.user_service import UserService


def migrate_existing_data():
    """Migrate existing projects and experiments to default user"""
    app = create_app()
    
    with app.app_context():
        print("Starting migration: Migrate Existing Projects/Experiments to Default User")
        print("=" * 70)
        
        # 1. Get or create default admin user
        print("\n1. Getting or creating default admin user...")
        admin = User.query.filter_by(is_admin=True).first()
        
        if not admin:
            # Create default admin user
            admin, error = UserService.create_user(
                username='admin',
                email='admin@mlstudio.local',
                password='admin123',
                profile_data={'display_name': 'Administrator'},
                is_admin=True
            )
            if error:
                print(f"   ⚠ Error creating admin user: {error}")
                return
            print(f"   ✓ Created default admin user: admin / admin123")
            print("   ⚠  IMPORTANT: Change the admin password immediately!")
        else:
            print(f"   ✓ Using existing admin user: {admin.username}")
        
        # 2. Assign projects without user_id to admin
        print("\n2. Assigning projects without user_id to admin...")
        projects_without_user = MLProject.query.filter_by(user_id=None).all()
        count = 0
        for project in projects_without_user:
            project.user_id = admin.id
            count += 1
        db.session.commit()
        print(f"   ✓ Assigned {count} projects to admin")
        
        # 3. Assign experiments without user_id to admin
        print("\n3. Assigning experiments without user_id to admin...")
        experiments_without_user = Experiment.query.filter_by(user_id=None).all()
        count = 0
        for experiment in experiments_without_user:
            # If experiment's project has a user_id, use that; otherwise use admin
            if experiment.project and experiment.project.user_id:
                experiment.user_id = experiment.project.user_id
            else:
                experiment.user_id = admin.id
            count += 1
        db.session.commit()
        print(f"   ✓ Assigned {count} experiments to admin")
        
        print("\n" + "=" * 70)
        print("Migration completed successfully!")
        print("=" * 70)


if __name__ == '__main__':
    migrate_existing_data()
