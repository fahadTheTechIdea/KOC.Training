# Demo Data Seeding Guide

This guide explains how to seed demo data for the KOC Training Platform.

## Quick Start

### Windows
```batch
seed_demo_data.bat
```

### Linux/Mac
```bash
chmod +x seed_demo_data.sh
./seed_demo_data.sh
```

### Direct Python (requires virtual environment)
```bash
python -m scripts.seed_demo_data
```

## Options

### Normal Seeding
Seeds all demo data (users, competitions, datasets, projects, discussions, models, activities):
```batch
seed_demo_data.bat
```

### Reset and Reseed
Clears existing demo data and reseeds everything:
```batch
seed_demo_data.bat --reset
```

### Seed Only Users
Creates only demo users without other data:
```batch
seed_demo_data.bat --users-only
```

## Using Flask CLI (Alternative)

If you have Flask CLI set up with `FLASK_APP` environment variable:

```bash
# Set FLASK_APP (Windows)
set FLASK_APP=app

# Set FLASK_APP (Linux/Mac)
export FLASK_APP=app

# Run seeding commands
flask seed-demo-data
flask seed-demo-data-reset
flask seed-demo-users
```

Or use Flask's app discovery:
```bash
flask --app app:create_app seed-demo-data
```

## Demo User Credentials

After seeding, you can log in with:
- **Username**: `demo`
- **Password**: `demo123`

Additional demo users are created as `demo_user_1` through `demo_user_12` with the same password.

## What Gets Seeded

- **13 Demo Users**: Main demo user + 12 additional users with KOC-style names
- **10 Competitions**: Mix of active and ended competitions (regression, classification, time series)
- **Participants & Submissions**: 15-25 participants per competition with realistic scores and rankings
- **8 Datasets**: Various categories with realistic metadata
- **10 Projects/Notebooks**: ML projects with code examples
- **20 Discussions**: With replies and upvotes
- **6 Models**: Published models from competitions
- **60+ Activities**: User activity logs

All demo data is tagged with `industry="demo"` for easy identification and filtering.

## Notes

- The seeding script is **idempotent** - you can run it multiple times safely
- Existing demo data will be skipped (unless using `--reset`)
- All data uses realistic KOC-relevant scenarios and terminology
- Demo data is visible to all users, not just the demo user

