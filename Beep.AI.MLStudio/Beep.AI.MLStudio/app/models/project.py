"""
ML Project Model
"""
from datetime import datetime
from app import db
import json


class MLProject(db.Model):
    """ML Project model"""
    __tablename__ = 'ml_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    template = db.Column(db.String(50), default='custom')  # classification, regression, clustering, etc.
    environment_name = db.Column(db.String(200), nullable=False)  # Virtual environment name in Host Admin
    status = db.Column(db.String(50), default='active')  # active, archived, deleted
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Nullable for backward compatibility
    is_shared = db.Column(db.Boolean, default=False)
    shared_with_users = db.Column(db.Text)  # JSON array of user IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Project configuration
    framework = db.Column(db.String(50))  # scikit-learn, tensorflow, pytorch, xgboost, etc.
    python_version = db.Column(db.String(20))
    
    # Industry module support
    industry_profile = db.Column(db.String(100))  # Industry profile ID (e.g., 'petroleum', 'finance')
    scenario_id = db.Column(db.String(100))  # Scenario within the profile
    industry_config = db.Column(db.Text)  # JSON - Industry-specific configuration
    
    # Competition integration
    competition_id = db.Column(db.Integer, nullable=True)  # Link to Community competition
    
    # Relationships
    experiments = db.relationship('Experiment', backref='project', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='projects')
    
    def get_shared_with_users(self):
        """Get shared_with_users as list"""
        if self.shared_with_users:
            try:
                return json.loads(self.shared_with_users)
            except:
                return []
        return []
    
    def set_shared_with_users(self, user_ids):
        """Set shared_with_users from list"""
        self.shared_with_users = json.dumps(user_ids) if user_ids else None
        self.is_shared = bool(user_ids)
    
    def add_shared_user(self, user_id):
        """Add user to shared list"""
        shared = self.get_shared_with_users()
        if user_id not in shared:
            shared.append(user_id)
            self.set_shared_with_users(shared)
    
    def remove_shared_user(self, user_id):
        """Remove user from shared list"""
        shared = self.get_shared_with_users()
        if user_id in shared:
            shared.remove(user_id)
            self.set_shared_with_users(shared)
    
    @property
    def experiments_count(self):
        """Get count of experiments for this project"""
        return len(self.experiments)
    
    def get_environment_info(self):
        """Get virtual environment information for this project"""
        from app.services.environment_manager import EnvironmentManager
        if not self.environment_name:
            return None
        try:
            env_mgr = EnvironmentManager()
            return env_mgr.get_environment(self.environment_name)
        except Exception:
            return None
    
    def validate_environment_link(self):
        """Validate that the project's virtual environment exists"""
        if not self.environment_name:
            return False, "Project has no environment_name set"
        try:
            from app.services.environment_manager import EnvironmentManager
            env_mgr = EnvironmentManager()
            env = env_mgr.get_environment(self.environment_name)
            if env:
                return True, "Environment exists and is valid"
            else:
                return False, f"Environment '{self.environment_name}' not found"
        except Exception as e:
            return False, f"Error checking environment: {str(e)}"
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        env_info = self.get_environment_info()
        
        # Parse industry config if present
        industry_config_data = None
        if self.industry_config:
            try:
                industry_config_data = json.loads(self.industry_config)
            except (json.JSONDecodeError, TypeError):
                industry_config_data = self.industry_config
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template': self.template,
            'environment_name': self.environment_name,
            'environment_exists': env_info is not None,
            'environment_path': env_info.path if env_info else None,
            'python_executable': env_info.python_executable if env_info else None,
            'status': self.status,
            'framework': self.framework,
            'python_version': self.python_version,
            'industry_profile': self.industry_profile,
            'scenario_id': self.scenario_id,
            'industry_config': industry_config_data,
            'competition_id': self.competition_id,
            'user_id': self.user_id,
            'is_shared': self.is_shared,
            'shared_with_users': self.get_shared_with_users(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'experiments_count': len(self.experiments)
        }
    
    def __repr__(self):
        return f'<MLProject {self.name}>'

