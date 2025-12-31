# KOC Training Platform - Integration Command Guide

This command provides comprehensive information about the Kuwait Oil Company (KOC) Machine Learning Training Platform integration project.

## Overview

This project integrates **Beep.AI.MLStudio** (ML development environment) and **Beep.AI.Community** (community platform) to create a comprehensive ML training and competition platform for **Kuwait Oil Company (KOC)**. The platform supports multiple departments including Oil & Gas (primary), Health & Medical, Energy & Sustainability, and Industrial Operations.

**KOC Website**: [https://www.kockw.com/sites/EN/Pages/Default.aspx](https://www.kockw.com/sites/EN/Pages/Default.aspx)

## Project Requirements

### Core Requirements

1. **Multi-Department Support**
   - Support multiple KOC departments (Oil & Gas, Health & Medical, Energy & Sustainability, Industrial)
   - Department-specific themes, icons, and branding
   - Department-aware challenges, teams, and progress tracking
   - Cross-department collaboration capabilities

2. **Authentication System**
   - **KEEP existing JWT authentication** - Do NOT replace it
   - **ADD Microsoft SSO (Azure AD)** as an additional authentication option
   - Users can choose between "Sign in with Email/Password" (JWT) or "Sign in with Microsoft" (SSO)
   - Unified token validation service for both methods
   - Support for both platforms (Community and MLStudio)

3. **UI/UX Enhancements**
   - Modern, responsive design with department-specific themes
   - Integration of icon assets from available icon packs
   - KOC branding (logo, colors, company information)
   - Accessibility compliance (WCAG)
   - Mobile and tablet optimization

4. **Platform Integration**
   - MLStudio can publish projects to Community platform
   - Deep linking between platforms
   - Shared authentication across platforms
   - API-based communication

5. **Competition & Learning Features**
   - Challenge creation and management
   - Team formation (within and across departments)
   - Leaderboards with department filtering
   - Progress tracking and certificates
   - Mentor/mentee matching system

### Technical Requirements

   Always asseume the machine does not have any python installed and we depending on pythonembedded

1. **Asset Management**
   - Organize icons by department from source folders
   - Copy relevant icons to project assets
   - Create asset registry and icon service
   - Optimize images for web use

2. **Database Schema**
   - Department model for multi-department support
   - User model extensions (department_id, Azure AD fields, auth_method)
   - Challenge, Submission, Team models with department support
   - Progress and Mentorship models

3. **API Endpoints**
   - Department management endpoints
   - Enhanced authentication endpoints (JWT + SSO)
   - Department-aware challenge endpoints
   - Cross-platform integration endpoints

## Rules and Guidelines

### Critical Rules

1. **DO NOT replace existing JWT authentication**
   - Keep all existing JWT routes and functionality
   - Add Microsoft SSO as an additional option
   - Both authentication methods must work simultaneously

2. **Preserve Existing Functionality**
   - Do not break existing features
   - Maintain backward compatibility
   - All existing users should continue to work

3. **Department Support**
   - Default department: Oil & Gas
   - All features must support department filtering
   - Users can belong to multiple departments
   - Challenges can be department-specific or cross-department

4. **Asset Organization**
   - Icons must be organized by department in `static/images/departments/`
   - Use PNG format for icons
   - Maintain asset manifest/registry
   - Optimize images for performance

5. **Branding Guidelines**
   - Use KOC official colors: Primary (#003366), Secondary (#FFD700)
   - Include KOC logo and company information
   - Support Arabic/English (RTL support for Arabic)
   - Professional, industrial aesthetic

### Implementation Guidelines

1. **Code Organization**
   - Follow existing project structure
   - Create new services for new functionality
   - Use blueprints for route organization
   - Maintain separation of concerns

2. **Database Migrations**
   - Create migrations for all schema changes
   - Support both SQLite (dev) and production databases
   - Ensure backward compatibility

3. **Error Handling**
   - Graceful error handling for all new features
   - User-friendly error messages
   - Logging for debugging

4. **Testing**
   - Unit tests for new models and services
   - Integration tests for API endpoints
   - UI tests for user interactions
   - Accessibility tests

5. **Documentation**
   - Update README files
   - Document API endpoints
   - Create user guides
   - Document department configuration

## Available Icon Assets

### Source Locations

1. **Laboratory Icons** (`3254044-laboratory`)
   - Path: `H:/dev/iconPacks/imgs/3254044-laboratory/3254044-laboratory/png/`
   - Use: Health & Medical department
   - Key icons: test tubes, microscope, scientist, DNA, vaccine

2. **Health Insurance Icons** (`4482096-health-insurance`)
   - Path: `H:/dev/iconPacks/imgs/4482096-health-insurance/4482096-health-insurance/png/`
   - Use: Health & Medical department
   - Key icons: health insurance, medical insurance, heart, protection

3. **Renewable Energy Icons** (`4514697-renewable-energy`)
   - Path: `H:/dev/iconPacks/imgs/4514697-renewable-energy/4514697-renewable-energy/png/`
   - Use: Energy & Sustainability department
   - Key icons: solar energy, wind energy, green energy, renewable energy

4. **Oil & Petroleum Icons** (`5725015-oil-and-petroleum`)
   - Path: `H:/dev/iconPacks/5725015-oil-and-petroleum/5725015-oil-and-petroleum/png/`
   - Use: Oil & Gas department (primary)
   - Key icons: offshore platform, oil tank, oil refinery, oil tanker

5. **Oil & Gas Industry Icons** (`6315514-oil-and-gas-industry`)
   - Path: `H:/dev/iconPacks/6315514-oil-and-gas-industry/6315514-oil-and-gas-industry/png/`
   - Use: Oil & Gas department
   - Key icons: oil drill, gas pipe, oil platform, gas station

6. **Oil & Gas Industry Icons** (`7258558-oil-and-gas-industry`)
   - Path: `H:/dev/iconPacks/7258558-oil-and-gas-industry/7258558-oil-and-gas-industry/png/`
   - Use: Oil & Gas department
   - Key icons: storage tank, offshore platform, oil truck, gas factory

7. **Industrial Process Icons** (`1064238-industrial-process`)
   - Path: `H:/dev/iconPacks/1064238-industrial-process/1064238-industrial-process/png/`
   - Use: Industrial Operations department
   - Key icons: engineer, factory, industrial robot, crane, conveyor

8. **Smart Meters Icons** (`6629098-smart-meters`)
   - Path: `H:/dev/iconPacks/imgs/6629098-smart-meters/`
   - Use: Energy & Sustainability department

9. **Sustainable Energy Icons** (`4815152-sustainable-energy`)
   - Path: `H:/dev/iconPacks/imgs/4815152-sustainable-energy/`
   - Use: Energy & Sustainability department

### Asset Organization Structure

```
Beep.AI.Community/static/images/
├── departments/
│   ├── oil-gas/
│   │   ├── icons/
│   │   │   ├── 001-offshore-platform.png
│   │   │   ├── 002-oil-tank.png
│   │   │   └── ... (from 5725015, 6315514, 7258558)
│   │   └── logo.png
│   ├── health-medical/
│   │   ├── icons/
│   │   │   ├── 001-bacterium.png
│   │   │   ├── 020-microscope.png
│   │   │   └── ... (from 3254044, 4482096)
│   │   └── logo.png
│   ├── energy-sustainability/
│   │   ├── icons/
│   │   │   ├── 060-solar-energy.png
│   │   │   ├── 084-wind-energy.png
│   │   │   └── ... (from 4514697, 6629098, 4815152)
│   │   └── logo.png
│   └── industrial/
│       ├── icons/
│       │   ├── 004-engineer.png
│       │   ├── 024-factory.png
│       │   └── ... (from 1064238)
│       └── logo.png
└── koc-branding/
    ├── logo.png
    └── favicon.ico
```

## Implementation Phases

### Phase 1: Asset Management & Multi-Department Setup (Week 1)
- Create asset copying script
- Copy and organize icons by department
- Create Department model and service
- Set up multi-theme CSS system
- Configure default departments
- Test department switching

### Phase 2: Authentication & Core Integration (Week 2)
- Set up Microsoft Azure AD application
- Add Microsoft SSO routes (keep existing JWT)
- Update user models (add optional Azure AD fields)
- Create unified token validation service
- Update login UI with both authentication options
- Implement API client for MLStudio → Community publishing
- Test both authentication flows

### Phase 3: UI/UX Foundation (Week 3)
- Integrate department-specific icons into UI
- Enhance Community dashboard with department themes
- Enhance MLStudio project management UI
- Implement responsive layouts
- Add accessibility features
- Apply KOC branding

### Phase 4: Competition Features (Week 4)
- Build challenge creation/management UI with department support
- Implement submission system
- Create interactive leaderboard (department-filtered)
- Add team formation interface (cross-department)
- Implement evaluation service

### Phase 5: Learning & Mentoring Features (Week 5)
- Implement progress tracking with visualizations
- Build certificate generation (department-aware)
- Create achievement/badge system
- Build mentor/mentee matching interface
- Implement review and feedback system

### Phase 6: Polish & Testing (Week 6)
- Cross-platform testing
- Performance optimization
- Accessibility audit
- User acceptance testing
- Documentation and training materials

## Key Features

### Authentication Features
- ✅ Local JWT authentication (existing, preserved)
- ✅ Microsoft SSO authentication (new, additional option)
- ✅ Unified token validation
- ✅ Single sign-on across platforms
- ✅ User choice of authentication method

### Department Features
- ✅ Multi-department support
- ✅ Department-specific themes
- ✅ Department-specific icons
- ✅ Department-aware challenges
- ✅ Cross-department teams
- ✅ Department filtering in leaderboards

### Competition Features
- ✅ Challenge creation and management
- ✅ Project submission from MLStudio
- ✅ Team formation (within/cross-department)
- ✅ Real-time leaderboards
- ✅ Automated evaluation
- ✅ Challenge templates

### Learning Features
- ✅ Progress tracking
- ✅ Module completion
- ✅ Certificate generation (PDF)
- ✅ Achievement badges
- ✅ Learning path recommendations

### Mentoring Features
- ✅ Mentor/mentee matching
- ✅ Project review system
- ✅ Code review interface
- ✅ Communication tools
- ✅ Review history and ratings

## Configuration

### Environment Variables

```bash
# Existing JWT Configuration (KEEP)
SECRET_KEY=<existing-secret-key>
JWT_SECRET_KEY=<existing-jwt-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=86400

# Microsoft Azure AD SSO (ADD - Optional)
AZURE_ENABLED=true
AZURE_CLIENT_ID=<koc-azure-app-client-id>
AZURE_CLIENT_SECRET=<koc-azure-app-secret>
AZURE_TENANT_ID=<koc-tenant-id>
AZURE_AUTHORITY=https://login.microsoftonline.com/<tenant-id>
AZURE_REDIRECT_URI_COMMUNITY=http://127.0.0.1:5002/auth/sso/callback
AZURE_REDIRECT_URI_MLSTUDIO=http://127.0.0.1:5001/auth/sso/callback
AZURE_SCOPE=User.Read openid profile email

# Platform URLs
COMMUNITY_URL=http://127.0.0.1:5002
MLSTUDIO_URL=http://127.0.0.1:5001

# KOC Multi-Department Configuration
DEFAULT_DEPARTMENT=oil-gas
DEPARTMENTS_ENABLED=oil-gas,health-medical,energy-sustainability,industrial
DEPARTMENT_THEME_SWITCHING=true

# KOC Branding
COMPANY_NAME=Kuwait Oil Company
COMPANY_NAME_AR=شركة نفط الكويت
COMPANY_WEBSITE=https://www.kockw.com
COMPANY_LOGO=/static/images/koc-branding/logo.png
PRIMARY_COLOR=#003366
SECONDARY_COLOR=#FFD700
```

## Expected Results

### Functional Results

1. **Unified Training Platform**
   - Seamless integration between MLStudio and Community
   - Users can develop ML projects in MLStudio and publish to Community
   - Single authentication system across both platforms

2. **Multi-Department Support**
   - Four departments configured and functional
   - Department-specific themes and icons
   - Department-aware challenges and competitions
   - Cross-department collaboration

3. **Enhanced User Experience**
   - Modern, responsive UI with department themes
   - Integrated icon assets throughout the platform
   - KOC branding consistently applied
   - Accessible and mobile-friendly

4. **Competition System**
   - Full challenge lifecycle (create, participate, evaluate)
   - Team formation and management
   - Real-time leaderboards
   - Automated scoring and evaluation

5. **Learning & Development**
   - Progress tracking and visualization
   - Certificate generation
   - Achievement system
   - Mentor/mentee matching

### Technical Results

1. **Authentication**
   - Both JWT and Microsoft SSO working
   - Unified token validation
   - Seamless user experience

2. **Asset Management**
   - Icons organized by department
   - Asset registry and service
   - Optimized for performance

3. **Database**
   - Department model implemented
   - User model extended
   - All new models created
   - Migrations completed

4. **API Integration**
   - MLStudio → Community publishing working
   - Deep linking between platforms
   - Department-aware endpoints

5. **UI/UX**
   - Department themes implemented
   - Icons integrated throughout
   - Responsive design
   - Accessibility compliant

## Success Metrics

- ✅ Both authentication methods working correctly
- ✅ Multi-department support functioning
- ✅ Department theme switching working
- ✅ Icon assets properly integrated
- ✅ SSO login success rate (if enabled)
- ✅ Number of active participants across departments
- ✅ Projects published from MLStudio to Community
- ✅ Cross-department team formations
- ✅ Mentor/mentee matches
- ✅ Certificate completions
- ✅ User engagement metrics by department
- ✅ UI/UX satisfaction scores
- ✅ Page load times and performance metrics

## Important Notes

1. **Never remove or replace existing JWT authentication** - it must remain functional
2. **All existing features must continue to work** - maintain backward compatibility
3. **Department support is mandatory** - all new features must be department-aware
4. **Asset organization is critical** - icons must be properly organized and accessible
5. **KOC branding is essential** - maintain professional, industrial aesthetic
6. **Accessibility is required** - WCAG compliance is mandatory
7. **Performance matters** - optimize assets and code for fast loading

## File Structure Reference

### Key Files to Create/Modify

**Community Platform**:
- `app/models/department.py` - Department model
- `app/models/challenge.py` - Challenge model (with department_id)
- `app/services/azure_auth.py` - Azure AD authentication
- `app/services/icon_service.py` - Icon management
- `app/routes/auth.py` - Enhanced auth routes (JWT + SSO)
- `app/routes/departments.py` - Department routes
- `static/css/themes/` - Department theme CSS files
- `static/images/departments/` - Organized icon assets
- `scripts/copy_assets.py` - Asset copying script

**MLStudio Platform**:
- `app/services/azure_auth.py` - Azure AD authentication
- `app/services/community_client.py` - Community API client
- `app/routes/auth.py` - Enhanced auth routes (JWT + SSO)
- `app/routes/api.py` - Enhanced with publish functionality

## Testing Checklist

- [ ] Both authentication methods (JWT and SSO) work
- [ ] Department switching and theming works
- [ ] Icons display correctly for each department
- [ ] MLStudio can publish projects to Community
- [ ] Challenges can be created and filtered by department
- [ ] Teams can be formed within and across departments
- [ ] Leaderboards filter correctly by department
- [ ] Progress tracking works with department awareness
- [ ] Certificates include department information
- [ ] Mentor matching works within and across departments
- [ ] UI is responsive on mobile and tablet
- [ ] Accessibility features work (keyboard navigation, screen readers)
- [ ] KOC branding is applied consistently
- [ ] Performance is acceptable (page load times)

## Support and Documentation

- KOC Website: https://www.kockw.com
- Project README files should be updated with new features
- API documentation should include all new endpoints
- User guides should cover department features
- Admin guides should cover department configuration

---

## Implementation Status

### ✅ Phase 1: Asset Management & Multi-Department Setup - COMPLETED
- Asset copying script created
- Department model and service implemented
- Icon service with manifest system
- All 4 department theme CSS files created
- Department initialization script ready

### ✅ Phase 2: Authentication & Core Integration - COMPLETED
- Microsoft SSO authentication added (alongside existing JWT)
- Unified token validation service
- User model updated with Azure AD support
- Login templates with dual authentication options
- SSO error handling

### ✅ Phase 3: UI/UX Foundation - COMPLETED
- Theme switching functionality implemented
- Icon integration with dynamic loading
- Enhanced dashboard with department selector
- Responsive design (mobile, tablet, desktop)
- Accessibility features (WCAG 2.1 AA compliance)

### ✅ Phase 4: Competition Features - COMPLETED
- Challenge model and routes implemented
- Submission system with evaluation
- Team formation and management
- Leaderboard with department filtering
- Evaluation service with MLStudio integration placeholder

### ✅ Phase 5: Learning & Mentoring Features - COMPLETED
- Progress tracking with visualizations
- Certificate generation (PDF with ReportLab)
- Achievement/badge system with automatic awarding
- Mentor/mentee matching algorithm
- Review and feedback system

## Next Steps

### 1. Initial Setup
```bash
# Copy assets from icon packs
python Beep.AI.Community/Beep.AI.Community/scripts/copy_assets.py

# Initialize database
python Beep.AI.Community/Beep.AI.Community/init_database.py

# Initialize departments
python Beep.AI.Community/Beep.AI.Community/scripts/init_departments.py

# Initialize achievements
python Beep.AI.Community/Beep.AI.Community/scripts/init_achievements.py
```

### 2. Configure Azure AD (Optional)
- Register application in Azure Portal
- Add credentials to `.env` file:
  ```
  AZURE_CLIENT_ID=your-client-id
  AZURE_CLIENT_SECRET=your-client-secret
  AZURE_TENANT_ID=your-tenant-id
  AZURE_REDIRECT_URI=http://localhost:5002/auth/sso/callback
  AZURE_ENABLED=true
  ```

### 3. MLStudio Integration
- Implement "Publish to Community" button in MLStudio UI
- Test project publishing workflow
- Verify challenge submission integration

### 4. Testing
- Test authentication (both JWT and SSO)
- Create challenges and test submission flow
- Test team formation and leaderboards
- Verify progress tracking and certificates
- Test mentorship matching

---

## Integration Guide

### Overview

This guide explains how to integrate **Beep.AI.MLStudio** and **Beep.AI.Community** platforms for the KOC Training Program. The integration enables seamless workflow from ML project development to community sharing and competition participation.

### Architecture

```
┌─────────────────────────┐         HTTP API         ┌──────────────────────────┐
│                         │  ──────────────────────> │                          │
│  Beep.AI.MLStudio       │                          │  Beep.AI.Community       │
│  (Port 5001)            │  <────────────────────── │  (Port 5002)             │
│                         │                          │                          │
│  - Project Development  │                          │  - Challenge Management  │
│  - Model Training       │                          │  - Team Formation        │
│  - Experiment Tracking  │                          │  - Leaderboards         │
│  - Publish to Community │                          │  - Progress Tracking    │
└─────────────────────────┘                          └──────────────────────────┘
```

### Integration Workflow

#### 1. Authentication Integration

Both platforms support shared authentication:

**Option A: JWT Authentication (Existing)**
- Users log in with username/password
- JWT tokens work across both platforms
- Tokens stored in localStorage/session

**Option B: Microsoft SSO (Optional)**
- Single sign-on via Azure AD
- Works across both platforms
- Enterprise authentication

**Configuration:**

```bash
# Community Platform (.env)
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_REDIRECT_URI=http://localhost:5002/auth/sso/callback
AZURE_ENABLED=true

# MLStudio Platform (.env)
AZURE_CLIENT_ID=your-client-id  # Same as Community
AZURE_CLIENT_SECRET=your-client-secret  # Same as Community
AZURE_TENANT_ID=your-tenant-id  # Same as Community
AZURE_REDIRECT_URI=http://localhost:5001/auth/sso/callback
AZURE_ENABLED=true
COMMUNITY_URL=http://127.0.0.1:5002
```

#### 2. Project Publishing Integration

**From MLStudio to Community:**

1. **Develop Project in MLStudio**
   - Create ML project
   - Train models
   - Evaluate results

2. **Publish to Community**
   - Click "Publish to Community" button in MLStudio
   - Select target challenge (optional)
   - Project metadata sent to Community API

3. **Community Processing**
   - Project appears in Community
   - If challenge selected, creates submission
   - Evaluation queued automatically

**API Integration Example:**

```python
# In MLStudio - Publish Project
import requests

def publish_to_community(project_id, project_name, challenge_id=None):
    """Publish MLStudio project to Community"""
    
    # Get authentication token
    token = get_auth_token()  # From localStorage or session
    
    # Prepare payload
    payload = {
        "project_id": project_id,
        "project_name": project_name,
        "project_url": f"http://127.0.0.1:5001/projects/{project_id}",
        "description": "My ML project description",
        "model_info": {
            "model_type": "RandomForest",
            "accuracy": 0.95,
            "metrics": {...}
        },
        "challenge_id": challenge_id  # Optional
    }
    
    # Send to Community
    response = requests.post(
        "http://127.0.0.1:5002/api/v1/mlstudio/publish-project",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Publish failed: {response.text}")
```

#### 3. Challenge Submission Workflow

**Complete Workflow:**

```
1. Admin creates challenge in Community
   └─> Challenge visible in MLStudio

2. User develops project in MLStudio
   └─> Trains model, evaluates results

3. User publishes project to challenge
   └─> POST /api/v1/mlstudio/publish-project
       { "project_id": 123, "challenge_id": 456 }

4. Community creates submission
   └─> Submission status: "pending"

5. Evaluation service processes
   └─> Submission status: "evaluating" → "completed"

6. Results appear in leaderboard
   └─> User can view ranking
```

**MLStudio Integration Code:**

```javascript
// In MLStudio UI - Publish Button Handler
async function publishToChallenge(projectId, challengeId) {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch('http://127.0.0.1:5002/api/v1/mlstudio/publish-project', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            project_id: projectId,
            project_name: getProjectName(projectId),
            project_url: `http://127.0.0.1:5001/projects/${projectId}`,
            challenge_id: challengeId,
            model_info: getModelInfo(projectId)
        })
    });
    
    if (response.ok) {
        const result = await response.json();
        showSuccessMessage('Project published successfully!');
        return result;
    } else {
        const error = await response.json();
        showErrorMessage(error.error || 'Failed to publish project');
    }
}
```

#### 4. Department-Aware Integration

**Department Context Flow:**

1. User selects department in Community
2. Department preference stored in user profile
3. MLStudio reads department from Community API
4. Challenges filtered by department
5. Teams can be department-specific or cross-department

**Department API Integration:**

```python
# Get user's current department
GET /api/v1/departments/current
Authorization: Bearer {token}

Response:
{
    "department": {
        "id": 1,
        "code": "oil-gas",
        "name": "Oil & Gas",
        "theme_css": "oil-gas-theme"
    }
}

# Get available challenges for department
GET /api/v1/mlstudio/challenges?department_id=1
Authorization: Bearer {token}

Response:
{
    "challenges": [
        {
            "id": 1,
            "title": "Oil Production Prediction",
            "department_id": 1,
            "status": "active",
            ...
        }
    ]
}
```

#### 5. Team Integration

**Cross-Platform Team Formation:**

1. User creates team in Community challenge
2. Team members can be from different departments
3. MLStudio projects can be submitted as team submissions
4. Leaderboard shows team rankings

**Team API Usage:**

```python
# Create team in Community
POST /api/v1/teams
{
    "challenge_id": 1,
    "name": "ML Experts Team",
    "description": "Our awesome team",
    "departments": ["oil-gas", "health-medical"]
}

# Submit project as team
POST /api/v1/mlstudio/publish-project
{
    "project_id": 123,
    "challenge_id": 1,
    "team_id": 5  # Team ID from Community
}
```

### Step-by-Step Integration Setup

#### Step 1: Verify Connection

**Test Community Connection from MLStudio:**

```bash
# From MLStudio, verify connection
curl http://127.0.0.1:5002/api/v1/mlstudio/verify-connection

Response:
{
    "status": "connected",
    "platform": "Beep.AI.Community",
    "version": "1.0.0"
}
```

#### Step 2: Configure URLs

**MLStudio Configuration (.env):**

```bash
# Community Platform URL
COMMUNITY_URL=http://127.0.0.1:5002

# For production
COMMUNITY_URL=https://community.koc-training.com
```

**Community Configuration (.env):**

```bash
# MLStudio Platform URL
MLSTUDIO_URL=http://127.0.0.1:5001

# For production
MLSTUDIO_URL=https://mlstudio.koc-training.com
```

#### Step 3: Implement Publish Button in MLStudio

**Add to MLStudio Project Page:**

```html
<!-- In MLStudio project template -->
<button id="publishBtn" class="btn btn-primary">
    Publish to Community
</button>

<script>
document.getElementById('publishBtn').addEventListener('click', async () => {
    const projectId = getCurrentProjectId();
    
    // Show challenge selector
    const challenges = await fetchChallenges();
    const challengeId = await showChallengeSelector(challenges);
    
    if (challengeId) {
        await publishToChallenge(projectId, challengeId);
    }
});
</script>
```

#### Step 4: Add Challenge List API Call

**In MLStudio - Fetch Available Challenges:**

```javascript
async function fetchAvailableChallenges() {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch(
        'http://127.0.0.1:5002/api/v1/mlstudio/challenges',
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );
    
    if (response.ok) {
        const data = await response.json();
        return data.challenges.filter(c => c.status === 'active');
    }
    
    return [];
}
```

### Integration Testing

#### Test 1: Connection Verification

```bash
# Test from MLStudio
curl http://127.0.0.1:5002/api/v1/mlstudio/verify-connection

# Expected: {"status": "connected", ...}
```

#### Test 2: Authentication Flow

1. Login to Community
2. Copy JWT token
3. Use token in MLStudio API calls
4. Verify token works for both platforms

#### Test 3: Project Publishing

1. Create project in MLStudio
2. Publish to Community
3. Verify project appears in Community
4. Check submission created (if challenge selected)

#### Test 4: Challenge Submission

1. Create challenge in Community
2. Publish project from MLStudio to challenge
3. Verify submission created
4. Check evaluation status
5. Verify leaderboard update

### Troubleshooting Integration

#### Issue: Connection Refused

**Symptoms:**
- MLStudio cannot connect to Community
- API calls fail with connection error

**Solutions:**
1. Verify Community is running on correct port
2. Check `COMMUNITY_URL` in MLStudio `.env`
3. Check firewall settings
4. Verify CORS configuration in Community

#### Issue: Authentication Failed

**Symptoms:**
- 401 Unauthorized errors
- Token validation fails

**Solutions:**
1. Verify JWT token is valid
2. Check token expiration
3. Ensure token is sent in Authorization header
4. Verify `JWT_SECRET_KEY` matches in both platforms

#### Issue: Department Not Found

**Symptoms:**
- Department filtering fails
- Challenges not showing for department

**Solutions:**
1. Verify departments initialized: `python scripts/init_departments.py`
2. Check user has department assigned
3. Verify department_id in API calls

#### Issue: Submission Not Created

**Symptoms:**
- Project published but no submission
- Challenge not found

**Solutions:**
1. Verify challenge_id is correct
2. Check challenge is active
3. Verify user has permission
4. Check submission limits

### API Reference

#### MLStudio Integration Endpoints

**Publish Project:**
```
POST /api/v1/mlstudio/publish-project
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
    "project_id": 123,
    "project_name": "My Project",
    "project_url": "http://mlstudio:5001/projects/123",
    "description": "Project description",
    "model_info": {...},
    "challenge_id": 456  # Optional
}

Response: 201 Created
{
    "message": "Project published successfully",
    "submission": {...}  # If challenge_id provided
}
```

**List Available Challenges:**
```
GET /api/v1/mlstudio/challenges?department_id=1&status=active
Authorization: Bearer {token}

Response: 200 OK
{
    "challenges": [...],
    "total": 5
}
```

**Verify Connection:**
```
GET /api/v1/mlstudio/verify-connection

Response: 200 OK
{
    "status": "connected",
    "platform": "Beep.AI.Community",
    "version": "1.0.0"
}
```

### Best Practices

1. **Error Handling**
   - Always handle API errors gracefully
   - Show user-friendly error messages
   - Log errors for debugging

2. **Token Management**
   - Store tokens securely
   - Handle token expiration
   - Refresh tokens when needed

3. **Department Context**
   - Always include department context
   - Filter challenges by user's department
   - Support cross-department collaboration

4. **User Experience**
   - Show loading states during API calls
   - Provide feedback on success/failure
   - Enable retry for failed operations

5. **Security**
   - Never expose tokens in URLs
   - Use HTTPS in production
   - Validate all inputs
   - Implement rate limiting

### Production Deployment

#### Environment Configuration

**Community Platform:**
```bash
COMMUNITY_URL=https://community.koc-training.com
MLSTUDIO_URL=https://mlstudio.koc-training.com
AZURE_REDIRECT_URI=https://community.koc-training.com/auth/sso/callback
```

**MLStudio Platform:**
```bash
COMMUNITY_URL=https://community.koc-training.com
AZURE_REDIRECT_URI=https://mlstudio.koc-training.com/auth/sso/callback
```

#### CORS Configuration

**In Community `app/__init__.py`:**
```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://mlstudio.koc-training.com",
            "http://127.0.0.1:5001"  # For development
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

#### SSL/TLS

- Use HTTPS for all production endpoints
- Configure SSL certificates
- Enable secure cookies
- Use secure token storage

---

**Last Updated**: Implementation Complete
**Status**: ✅ All Phases Completed - Ready for Testing
**Priority**: High - KOC Training Program
**Version**: 1.0.0
