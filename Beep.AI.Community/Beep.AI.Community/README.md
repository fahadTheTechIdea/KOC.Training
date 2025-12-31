# Beep.AI.Community Platform

A simple, friendly platform where **everyone** can share data, create projects, and learn together - no technical background required!

## Vision

Beep.AI.Community makes machine learning accessible to everyone. Whether you're a student, business professional, or curious explorer, you can:
- 📊 **Share Data** - Easy data sharing with simple uploads
- 🚀 **Explore Projects** - Browse and learn from others' work visually  
- 🎯 **Join Challenges** - Participate in friendly competitions with guided steps
- 💬 **Learn Together** - Community support and tutorials built-in
- 🔗 **Use MLStudio** - Publish your MLStudio projects with one click

## Quick Start

### Installation vs Configuration

**Important**: This platform separates **installation** (handled by startup script) from **configuration** (handled by Setup Wizard).

- **Installation** (Startup Script): Downloads embedded Python, installs packages, sets up environment
- **Configuration** (Setup Wizard): Configures database, authentication mode, branding, creates admin account

### 1. Run Startup Script

#### Quick Start (Recommended)

Use the platform-specific launchers for automatic setup:

- **Windows**: 
  ```batch
  run.bat
  ```
  Or simply double-click `run.bat` in Windows Explorer

- **Linux/macOS**: 
  ```bash
  ./run.sh
  ```

- **macOS (Double-click)**: 
  Double-click `run.command` to open Terminal and run automatically

#### Advanced: Manual Python Launcher

Alternatively, run the Python launcher directly:

```bash
python run_community.py
```

**Command-line options:**
```bash
python run_community.py --port=5003          # Custom port
python run_community.py --host=0.0.0.0       # Listen on all interfaces
python run_community.py --debug              # Enable debug mode
python run_community.py --no-browser         # Don't open browser automatically
```

#### What the Launchers Do

**All launcher scripts automatically handle**:
- ✅ Downloads/installs embedded Python (if needed)
- ✅ Creates virtual environment using embedded Python (or system Python)
- ✅ Installs ALL Python packages from `requirements.txt` (including all database drivers)
- ✅ Creates `.env` file from `.env.example` (if missing)
- ✅ Creates necessary directories (`uploads/`, `instance/`, etc.)
- ✅ Verifies critical dependencies
- ✅ Starts the Flask application

**Note**: System-level database servers (PostgreSQL, MySQL, SQL Server, etc.) must be installed separately. Only SQLite is file-based and doesn't require a server.

#### Manual Embedded Python Setup (Optional)

If you prefer to set up embedded Python manually before running:

- **Windows**: Run `setup_embedded_python.bat`
- **Linux/macOS**: Run `./setup_embedded_python.sh`

This will download and configure embedded Python independently, which you can then use for creating virtual environments.

### 2. Setup Wizard (First Run Only)

On first run, you'll be automatically redirected to the **Setup Wizard** which handles application-level installation and configuration:

**Step 1: Admin Account Creation**
- Create the first admin user (username, email, password)

**Step 2: Database Configuration**
- Select database provider: SQLite, PostgreSQL, MySQL/MariaDB, SQL Server, Oracle, or Firebird
- Enter connection string (examples provided for each provider)
- Test database connection

**Step 3: Authentication Mode**
- **Local JWT**: Simple local authentication (default for standalone deployments)
- **Identity Server OAuth2/OIDC**: Enterprise authentication via Beep.Foundation.IdentityServer (for enterprise/company deployments)

**Step 4: Branding Configuration**
- Choose industry theme (Oil & Gas, Finance, General, etc.)
- Set company name and upload logo
- Customize application appearance

**Step 5: Complete Setup**
- Creates database schema
- Initializes application state
- Redirects to main application

**The Setup Wizard does NOT install**:
- Python or embedded Python (handled by startup script)
- Python packages or dependencies (handled by startup script)
- System database servers (must be installed separately)
- Virtual environments (handled by startup script)

### 4. Access the Application

After setup, the application will be available at: **http://127.0.0.1:5002**

**First Login**:
- **Username**: The admin username you created in setup wizard
- **Password**: The password you set during setup

## Features

### For Everyone
- 🎨 **Simple, Visual Interface** - No technical jargon
- 📱 **Mobile-Friendly** - Works on any device
- 💡 **Help Everywhere** - Tooltips, tutorials, and AI assistance
- 🔍 **Easy Search** - Find anything quickly

### For Data Sharers
- 📤 **One-Click Upload** - Drag & drop files
- 🤖 **Auto-Description** - AI helps describe your data
- 👁️ **Visual Preview** - See your data in beautiful tables and charts
- 🔒 **Privacy Controls** - Public/Friends/Private sharing

### For MLStudio Users
- 🔗 **One-Click Publish** - Share projects directly from MLStudio
- 👀 **Project Gallery** - Showcase your work visually
- 🎯 **Challenge Integration** - Submit to competitions easily

### For Learners
- 📚 **Example Projects** - Learn from real examples
- 🎓 **Getting Started Guide** - Step-by-step tutorials
- 💬 **Community Help** - Ask questions, get answers
- 🏆 **Friendly Challenges** - Learn by doing

### White-Label & Branding
- 🎨 **Industry Themes** - Pre-configured themes for Oil & Gas, Finance, etc.
- 🏢 **Company Branding** - Customize logos, colors, company name
- 🔧 **Dynamic Theming** - Users can switch themes
- 📦 **Deployment Ready** - Package for specific industries

## Integration

### MLStudio Integration
MLStudio can publish projects, datasets, and models to this platform via REST API. See API documentation at `/api/v1/docs`.

### Beep.AI.Server Integration
Leverages Beep.AI.Server for:
- 🤖 AI-powered features (auto-descriptions, code suggestions)
- 🧠 LLM services for community help
- 📊 Model hosting and deployment

## API Documentation

Once running, API documentation is available at:
- **Swagger UI**: http://127.0.0.1:5002/api/v1/docs
- **ReDoc**: http://127.0.0.1:5002/api/v1/redoc

## Development

### Running in Development Mode

#### Using Launcher Scripts (Recommended)

**Windows:**
```batch
run.bat --debug
```

**Linux/macOS:**
```bash
./run.sh --debug
```

#### Direct Python Execution

```bash
# Set environment variable
export FLASK_ENV=development  # Windows: set FLASK_ENV=development

# Run via launcher
python run_community.py --debug

# Or run directly (requires manual setup)
python run.py
```

### Troubleshooting

#### Embedded Python Download Issues

If automatic download fails:

1. **Windows**: Run `setup_embedded_python.bat` manually
2. **Linux/macOS**: Run `./setup_embedded_python.sh` manually
3. Or use system Python (the launcher will fallback automatically on Linux/macOS)

#### Port Already in Use

If port 5002 is already in use, specify a different port:

```bash
# Windows
run.bat --port=5003

# Linux/macOS
./run.sh --port=5003

# Python launcher
python run_community.py --port=5003
```

#### Permission Issues (Linux/macOS)

Make launcher scripts executable:

```bash
chmod +x run.sh
chmod +x run.command
chmod +x setup_embedded_python.sh
chmod +x run_community.py
```

#### Missing Dependencies

If dependencies fail to install:

1. Check internet connection
2. Verify `requirements.txt` exists
3. Try running setup manually:
   ```bash
   python -m pip install -r requirements.txt
   ```

### Running Migrations

```bash
flask db init          # First time only
flask db migrate -m "Description"
flask db upgrade
```

## License

MIT License - See LICENSE file for details

---

**Made with ❤️ for the ML community - Making ML accessible to everyone!**
