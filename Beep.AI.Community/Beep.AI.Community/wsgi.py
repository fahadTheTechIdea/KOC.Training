"""
WSGI entry point for KOC A.I. Digital Campus on PythonAnywhere
This file is used by PythonAnywhere to serve the Flask application.
"""
import sys
import os
import secrets

# Add the application directory to the Python path
# Update 'yourusername' with your PythonAnywhere username
path = '/home/fahadal70/KOC.Training/Beep.AI.Community/Beep.AI.Community'
if path not in sys.path:
    sys.path.insert(0, path)

# Change to the application directory
os.chdir(path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'wsgi.py'

# Set DATABASE_URL if not already set (default to SQLite in instance folder)
if 'DATABASE_URL' not in os.environ:
    # Create instance directory if it doesn't exist
    instance_dir = os.path.join(path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    # Set default SQLite database path
    os.environ['DATABASE_URL'] = f'sqlite:///{os.path.join(instance_dir, "community.db")}'

# Set SECRET_KEY if not already set (generate a random one)
if 'SECRET_KEY' not in os.environ:
    os.environ['SECRET_KEY'] = secrets.token_hex(32)

# Set JWT_SECRET_KEY if not already set (use SECRET_KEY as default)
if 'JWT_SECRET_KEY' not in os.environ:
    os.environ['JWT_SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Import the Flask app
from app import create_app

# Create the application instance
application = create_app(config_name='production')

if __name__ == "__main__":
    application.run()

