# Beep.AI.Community - Architecture Documentation

## Overview

Beep.AI.Community is a collaborative platform for ML competitions, learning, and knowledge sharing. It provides challenge management, team formation, leaderboards, progress tracking, and integration with MLStudio for project publishing.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Beep.AI.Community Platform                     │
│                  (Flask + REST API)                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
│   Web UI     │   │  Competition    │  │  MLStudio   │
│  (Templates) │   │  Service        │  │  Integration │
└──────────────┘   └──────────────────┘  └─────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
│   Database   │   │  File Storage   │  │  Auth        │
│  (SQLite)    │   │  (Uploads)      │  │  (JWT/SSO)   │
└──────────────┘   └──────────────────┘  └─────────────┘
```

## Core Components

### 1. Competition System

**Purpose**: Manages ML challenges, submissions, and leaderboards

**Key Files**:
- `app/models/competition.py` - Competition model
- `app/models/submission.py` - Submission model
- `app/services/competition_service.py` - Competition logic
- `app/services/scoring_service.py` - Scoring and evaluation
- `app/services/submission_evaluator.py` - Submission evaluation

**Competition Lifecycle**:
1. Admin creates competition with dataset and scoring script
2. Users form teams (optional)
3. Users develop models in MLStudio
4. Users publish projects to competition (creates submission)
5. System evaluates submissions automatically
6. Leaderboard updates with rankings

**Submission Evaluation**:
- Scoring script provided by admin
- Executes in isolated environment
- Captures metrics (accuracy, F1, etc.)
- Results stored in submission record

### 2. Dataset Management

**Purpose**: Manages competition datasets and data splits

**Key Files**:
- `app/models/dataset.py` - Dataset model
- `app/services/dataset_service.py` - Dataset operations
- `app/services/dataset_split_service.py` - Train/test splitting

**Features**:
- Dataset upload and storage
- Train/test split management
- Dataset versioning
- Access control (competition-specific)

### 3. User Participation

**Purpose**: Tracks user engagement and progress

**Key Files**:
- `app/models/activity.py` - Activity tracking
- `app/services/profile_service.py` - User profile management

**Tracking**:
- Challenge participation
- Submission history
- Team memberships
- Progress metrics

### 4. Discussion System

**Purpose**: Enables community discussions and Q&A

**Key Files**:
- `app/models/discussion.py` - Discussion model
- `app/services/discussion_service.py` - Discussion management

**Features**:
- Threaded discussions
- Competition-specific forums
- User mentions and notifications

### 5. Model Registry

**Purpose**: Stores and manages trained models

**Key Files**:
- `app/models/model_registry.py` - Model registry model
- `app/services/model_registry_service.py` - Model management
- `app/services/model_validator.py` - Model validation

**Features**:
- Model upload and storage
- Model versioning
- Model validation
- Model sharing

### 6. MLStudio Integration

**Purpose**: Receives and processes projects from MLStudio

**Key Files**:
- `app/routes/api/v1/` - API endpoints
- `app/services/project_service.py` - Project management

**Integration Flow**:
```
MLStudio → POST /api/v1/mlstudio/publish-project
         → Creates submission (if challenge_id provided)
         → Queues evaluation
         → Updates leaderboard
```

**API Endpoints**:
- `POST /api/v1/mlstudio/publish-project` - Publish project
- `GET /api/v1/mlstudio/challenges` - List available challenges
- `GET /api/v1/mlstudio/verify-connection` - Connection test

**Configuration**:
- MLStudio connection configurable via config file
- Admin can embed MLStudio URL in app
- Supports both manual and automatic connection

### 7. Authentication System

**Purpose**: Handles user authentication (JWT + SSO)

**Key Files**:
- `app/services/auth_service.py` - JWT authentication
- `app/services/identity_server_auth_service.py` - SSO support
- `app/models/user.py` - User model

**Authentication Methods**:
1. **JWT (Local)**: Username/password, token-based
2. **Microsoft SSO**: Azure AD integration (optional)
3. **Identity Server**: External OAuth provider (optional)

**Token Management**:
- JWT tokens for API access
- Token expiration and refresh
- Unified validation for both methods

### 8. Department Support

**Purpose**: Multi-department organization for KOC

**Key Files**:
- `app/services/theme_service.py` - Department themes
- `app/static/css/themes/` - Department CSS files

**Features**:
- Department-specific themes
- Department-aware challenges
- Cross-department teams
- Department filtering in leaderboards

## Data Flow: Competition Submission

```
┌─────────────┐
│   MLStudio  │
│   User      │
└──────┬──────┘
       │
       │ POST /api/v1/mlstudio/publish-project
       │ {project_id, challenge_id, ...}
       ▼
┌──────────────────────┐
│  Community API       │
│  - Validates token   │
│  - Creates submission│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Submission Model    │
│  (status: pending)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  SubmissionEvaluator │
│  - Downloads model   │
│  - Runs scoring      │
│  - Calculates metrics│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Submission Model    │
│  (status: completed) │
│  (score: X.XX)       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Leaderboard Update  │
│  (Rankings refresh)  │
└──────────────────────┘
```

## Database Schema

### Core Tables

**users**
- `id`, `username`, `email`, `password_hash`
- `department_id` (KOC department)
- `auth_method` (jwt, sso, identity_server)
- `azure_ad_id` (for SSO users)

**competitions**
- `id`, `title`, `description`
- `dataset_id`, `scoring_script_path`
- `department_id` (KOC department)
- `start_date`, `end_date`, `status`

**submissions**
- `id`, `competition_id`, `user_id`, `team_id`
- `project_id` (from MLStudio)
- `status` (pending, evaluating, completed, failed)
- `score`, `metrics` (JSON)
- `submitted_at`, `evaluated_at`

**teams**
- `id`, `competition_id`, `name`
- `department_ids` (JSON array for cross-department)
- `members` (relationship)

**datasets**
- `id`, `name`, `description`
- `file_path`, `file_size`
- `train_split_path`, `test_split_path`
- `competition_id`

## API Endpoints

### Competitions
- `GET /api/v1/competitions` - List competitions
- `POST /api/v1/competitions` - Create competition (admin)
- `GET /api/v1/competitions/{id}` - Get competition
- `GET /api/v1/competitions/{id}/leaderboard` - Get leaderboard

### Submissions
- `GET /api/v1/submissions` - List submissions
- `POST /api/v1/submissions` - Create submission
- `GET /api/v1/submissions/{id}` - Get submission
- `GET /api/v1/submissions/{id}/results` - Get results

### MLStudio Integration
- `POST /api/v1/mlstudio/publish-project` - Publish project
- `GET /api/v1/mlstudio/challenges` - List challenges
- `GET /api/v1/mlstudio/verify-connection` - Test connection

### Departments
- `GET /api/v1/departments` - List departments
- `GET /api/v1/departments/current` - Get user's department
- `PUT /api/v1/departments/current` - Set user's department

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Frontend**: Jinja2 templates, Bootstrap, JavaScript
- **Database**: SQLite (dev), PostgreSQL (production)
- **Authentication**: Flask-JWT-Extended, MSAL (for SSO)
- **File Storage**: Local filesystem (uploads/)
- **API**: RESTful API with JSON responses

## Key Design Patterns

1. **Application Factory**: Flask app created via `create_app()`
2. **Service Layer**: Business logic in services
3. **Blueprint Pattern**: Route organization via Flask blueprints
4. **Repository Pattern**: Models abstract database access
5. **Strategy Pattern**: Different auth strategies (JWT, SSO)

## Security Considerations

- JWT token authentication
- Password hashing (bcrypt)
- CORS configuration
- Rate limiting (Flask-Limiter)
- Input validation and sanitization
- File upload restrictions

## Performance Optimizations

- Database indexing on frequently queried fields
- Lazy loading of relationships
- Caching of leaderboard data
- Pagination for large result sets
- Static file serving optimization

## Configuration Management

### Environment Variables
- Database connection
- JWT secrets
- Azure AD credentials (optional)
- MLStudio URL
- Community URL

### Config File Support (Planned)
- `config.json` or `config.yaml` for admin configuration
- MLStudio-Community connection settings
- Embeddable in app for easy deployment
- Overrides environment variables

## Future Enhancements

- Real-time leaderboard updates (WebSocket)
- Advanced analytics and visualizations
- Certificate generation (PDF)
- Achievement/badge system
- Mentor/mentee matching
- Mobile app support
- Multi-language support (Arabic/English)

