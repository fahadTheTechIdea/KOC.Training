"""
Run Beep.AI.Community Platform
"""
import os
import sys
import argparse
from app import create_app, db
from app.database import init_db

app = create_app()

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Beep.AI.Community Platform')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 5001)), help='Port number')
    parser.add_argument('--host', type=str, default=os.getenv('HOST', '127.0.0.1'), help='Host address')
    parser.add_argument('--debug', action='store_true', default=os.getenv('DEBUG', 'false').lower() == 'true', help='Enable debug mode')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    
    args = parser.parse_args()
    
    # Initialize database if needed
    with app.app_context():
        db_file = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if db_file and not os.path.exists(db_file):
            init_db()
            print(f"Database initialized at {db_file}")
    
    host = args.host
    port = args.port
    debug = args.debug
    
    print(f"Starting Beep.AI.Community on http://{host}:{port}")
    
    # Open browser automatically if not disabled
    if not args.no_browser:
        try:
            import webbrowser
            import threading
            def open_browser():
                import time
                time.sleep(1.5)  # Wait for server to start
                webbrowser.open(f'http://{host}:{port}')
            threading.Thread(target=open_browser, daemon=True).start()
        except Exception:
            pass  # Fail silently if browser can't be opened
    
    app.run(host=host, port=port, debug=debug)
