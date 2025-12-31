# Deploying KOC Training Platform to PythonAnywhere

This guide explains how to deploy both **Beep.AI.MLStudio** and **Beep.AI.Community** applications to PythonAnywhere.

## Prerequisites

1. A PythonAnywhere account (free tier available)
2. Git installed on your local machine
3. Both applications working locally

## Step 1: Prepare Your Applications

### Option A: Upload via Git (Recommended)

1. **Create a Git repository** (if not already done):
   ```bash
   cd KOC.Training
   git init
   git add .
   git commit -m "Initial commit for PythonAnywhere deployment"
   git remote add origin <your-git-repo-url>
   git push -u origin main
   ```

2. **On PythonAnywhere**, clone the repository:
   ```bash
   cd ~
   git clone <your-git-repo-url>
   ```

### Option B: Upload via Files Tab

1. Zip your application folders
2. Upload via PythonAnywhere's Files tab
3. Extract in your home directory

## What to Copy and What to Exclude

### ✅ **INCLUDE These Files/Folders:**
- `app/` - All application code
- `templates/` - HTML templates
- `static/` - CSS, JS, images, assets
- `migrations/` - Database migration files
- `scripts/` - Utility scripts (if needed)
- `requirements.txt` - Python dependencies
- `wsgi.py` - WSGI entry point (update paths!)
- `config.example.json` - Configuration template
- `README.md` - Documentation (optional)

### ❌ **EXCLUDE These Files/Folders:**
- `python-embedded/` - **Windows-specific, NOT needed on Linux**
- `.venv/` or `venv/` - **Will be created on PythonAnywhere**
- `__pycache__/` - Python cache files
- `*.db` or `*.sqlite` - Database files (will be created fresh)
- `instance/` - Local instance folder (will be created)
- `.env` - Environment variables (configure via Web tab instead)
- `uploads/` - User uploads (can recreate structure, but empty is fine)
- `*.log` - Log files
- `.git/` - Git repository (if using Git, clone instead)
- `run.bat`, `run.sh`, `run.command` - Local run scripts (not needed)
- `setup_embedded_python.*` - Windows setup scripts

### Quick Copy Command (if using Git):
The easiest way is to use Git (Option A above). If you must copy manually, create a zip excluding the above items.

## Step 2: Set Up Python Environment

### For Beep.AI.Community:

1. **Open a Bash console** on PythonAnywhere
2. **Navigate to the application directory**:
   ```bash
   cd ~/KOC.Training/Beep.AI.Community/Beep.AI.Community
   ```

3. **Create a virtual environment**:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### For Beep.AI.MLStudio:

1. **Navigate to MLStudio directory**:
   ```bash
   cd ~/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio
   ```

2. **Create a virtual environment**:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Step 3: Configure WSGI Files

### For Beep.AI.Community:

1. **Edit the `wsgi.py` file** in `Beep.AI.Community/Beep.AI.Community/`:
   - Replace `yourusername` with your PythonAnywhere username
   - Update the path if your directory structure is different

2. **In PythonAnywhere Web tab**:
   - Click "Add a new web app"
   - Select "Manual configuration"
   - Select Python 3.10
   - In the WSGI configuration file, point to:
     ```
     /home/yourusername/KOC.Training/Beep.AI.Community/Beep.AI.Community/wsgi.py
     ```

### For Beep.AI.MLStudio:

1. **Edit the `wsgi.py` file** in `Beep.AI.MLStudio/Beep.AI.MLStudio/`:
   - Replace `yourusername` with your PythonAnywhere username
   - Update the path if your directory structure is different

2. **Create a second web app** (if you have a paid account) or use a subdomain:
   - Click "Add a new web app" (or configure subdomain)
   - Select "Manual configuration"
   - Select Python 3.10
   - In the WSGI configuration file, point to:
     ```
     /home/yourusername/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio/wsgi.py
     ```

## Step 4: Configure Environment Variables

### For Beep.AI.Community:

1. **In PythonAnywhere Web tab**, scroll to "Environment variables"
2. **Add the following variables**:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///home/yourusername/KOC.Training/Beep.AI.Community/Beep.AI.Community/instance/community.db
   JWT_SECRET_KEY=your-jwt-secret-key-here
   ```

### For Beep.AI.MLStudio:

1. **Add environment variables**:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///home/yourusername/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio/instance/mlstudio.db
   JWT_SECRET_KEY=your-jwt-secret-key-here
   ```

## Step 5: Initialize Databases

### For Beep.AI.Community:

1. **Open a Bash console** and activate the virtual environment:
   ```bash
   cd ~/KOC.Training/Beep.AI.Community/Beep.AI.Community
   source venv/bin/activate
   ```

2. **Initialize the database**:
   ```bash
   flask db upgrade
   # Or if using create_all:
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

3. **Run setup** (if needed):
   ```bash
   flask setup
   ```

### For Beep.AI.MLStudio:

1. **Activate the virtual environment**:
   ```bash
   cd ~/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio
   source venv/bin/activate
   ```

2. **Initialize the database**:
   ```bash
   flask db upgrade
   # Or if using create_all:
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

## Step 6: Configure Static Files and Paths

### For Beep.AI.Community:

1. **In PythonAnywhere Web tab**, scroll to "Static files"
2. **Add static file mappings**:
   ```
   URL: /static
   Directory: /home/yourusername/KOC.Training/Beep.AI.Community/Beep.AI.Community/static
   ```

### For Beep.AI.MLStudio:

1. **Add static file mappings**:
   ```
   URL: /static
   Directory: /home/yourusername/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio/static
   ```

## Step 7: Configure Application URLs

### For Beep.AI.Community:

1. **In Web tab**, set:
   - **Source code**: `/home/yourusername/KOC.Training/Beep.AI.Community/Beep.AI.Community`
   - **Working directory**: `/home/yourusername/KOC.Training/Beep.AI.Community/Beep.AI.Community`
   - **Virtualenv**: `/home/yourusername/KOC.Training/Beep.AI.Community/Beep.AI.Community/venv`

### For Beep.AI.MLStudio:

1. **Set**:
   - **Source code**: `/home/yourusername/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio`
   - **Working directory**: `/home/yourusername/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio`
   - **Virtualenv**: `/home/yourusername/KOC.Training/Beep.AI.MLStudio/Beep.AI.MLStudio/venv`

## Step 8: Update Configuration Files

### Update Community Connection (if needed):

1. **Create `community_config.json`** in `Beep.AI.Community/Beep.AI.Community/`:
   ```json
   {
     "mlstudio_connection": {
       "url": "https://yourusername.pythonanywhere.com/mlstudio",
       "enabled": true,
       "api_key": "",
       "timeout": 10
     }
   }
   ```

### Update MLStudio Connection (if needed):

1. **Create `mlstudio_config.json`** in `Beep.AI.MLStudio/Beep.AI.MLStudio/`:
   ```json
   {
     "mlstudio": {
       "community_connection": {
         "url": "https://yourusername.pythonanywhere.com/community",
         "enabled": true,
         "api_key": "",
         "timeout": 10
       }
     }
   }
   ```

## Step 9: Reload Web Apps

1. **Click the green "Reload" button** in the Web tab for both applications
2. **Check the error logs** if there are any issues:
   - Click "Error log" link in the Web tab

## Step 10: Access Your Applications

- **Community**: `https://yourusername.pythonanywhere.com/community` (or your custom domain)
- **MLStudio**: `https://yourusername.pythonanywhere.com/mlstudio` (or your custom domain/subdomain)

## Troubleshooting

### Common Issues:

1. **Import Errors**:
   - Check that all dependencies are installed in the virtual environment
   - Verify the Python path in `wsgi.py` is correct

2. **Database Errors**:
   - Ensure the database file path is correct
   - Check file permissions on the database directory

3. **Static Files Not Loading**:
   - Verify static file mappings in the Web tab
   - Check that static files exist in the correct directory

4. **500 Internal Server Error**:
   - Check the error log in the Web tab
   - Verify all environment variables are set correctly
   - Ensure the virtual environment is activated

### Viewing Logs:

1. **Error logs**: Click "Error log" in the Web tab
2. **Server logs**: Check the console output in the Web tab
3. **Application logs**: Check files in the `logs/` directory (if configured)

## Notes

- **Free accounts** on PythonAnywhere can only host one web app. You'll need a paid account to host both applications simultaneously, or use subdomains if available.
- **Database**: SQLite works for small applications. For production, consider PostgreSQL (available on paid accounts).
- **File uploads**: Be aware of file size limits on free accounts.
- **Scheduled tasks**: Use the "Tasks" tab to set up cron jobs if needed.

## Alternative: Single Application Deployment

If you can only deploy one application:

1. Deploy **Community** as the main application
2. Configure MLStudio connection to point to a local instance or another hosting service
3. Or deploy **MLStudio** and configure Community connection accordingly

## Support

For PythonAnywhere-specific issues, check:
- [PythonAnywhere Help](https://help.pythonanywhere.com/)
- [PythonAnywhere Community Forum](https://www.pythonanywhere.com/forums/)

