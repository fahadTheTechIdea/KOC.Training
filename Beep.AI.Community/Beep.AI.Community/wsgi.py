"""
WSGI entry point for Beep.AI.Community on PythonAnywhere
This file is used by PythonAnywhere to serve the Flask application.
"""
import sys
import os

# Add the application directory to the Python path
# Update 'yourusername' with your PythonAnywhere username
path = '/home/yourusername/KOC.Training/Beep.AI.Community/Beep.AI.Community'
if path not in sys.path:
    sys.path.insert(0, path)

# Change to the application directory
os.chdir(path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'wsgi.py'

# Import the Flask app
from app import create_app

# Create the application instance
application = create_app(config_name='production')

if __name__ == "__main__":
    application.run()

