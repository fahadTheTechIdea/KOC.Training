# Beep.AI.MLStudio - Architecture Documentation

## Overview

Beep.AI.MLStudio is a visual machine learning workflow platform that enables users to build, train, and deploy ML models through a drag-and-drop interface. The platform converts visual workflows into executable Python code and manages the complete ML lifecycle.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Beep.AI.MLStudio                         │
│                  (Flask + SocketIO)                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
│   Frontend   │   │  Workflow Engine │  │  ML Service │
│  (ReactFlow) │   │  (Code Gen)      │  │  (Training) │
└──────────────┘   └──────────────────┘  └─────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
│   Database   │   │  Project Store  │  │  Community  │
│  (SQLite)    │   │  (File System)  │  │  Platform   │
└──────────────┘   └─────────────────┘  └─────────────┘
```

## Core Components

### 1. Workflow Engine

**Purpose**: Converts visual workflow graphs into executable Python code

**Key Files**:
- `app/models/workflow.py` - Workflow data model
- `app/services/workflow_service.py` - Code generation logic
- `app/services/workflow_executor.py` - Execution order determination

**How It Works**:

1. **Visual Workflow Definition**
   - Users create workflows using ReactFlow (nodes and edges)
   - Workflow stored as JSON in `workflow_data` field
   - Structure: `{nodes: [...], edges: [...], viewport: {...}}`

2. **Topological Sorting**
   - `WorkflowExecutor` analyzes node dependencies
   - Determines execution order using topological sort
   - Validates workflow for cycles and missing connections

3. **Code Generation**
   - `WorkflowService.generate_code_from_workflow()` processes nodes in order
   - Each node type has a code generator method
   - Generates imports, data loading, preprocessing, training, evaluation code
   - Handles variable passing between nodes

4. **Node Types Supported**:
   - **Data Loading**: `data_load_csv`, `data_load_json`, `data_load_excel`
   - **Preprocessing**: `preprocess_split`, `preprocess_scale`, `preprocess_encode`, `auto_data_prep`
   - **Feature Selection**: `preprocess_select_features_target`
   - **Model Training**: `classifier_*`, `regressor_*` (framework-specific)
   - **Evaluation**: `evaluate`, `calculate_metrics`
   - **Model Saving**: `save_model`

**Example Workflow Execution**:
```
Start → Load Data → Auto Prep → Select Features → Split → Scale → Train → Evaluate → Save
```

### 2. ML Service

**Purpose**: Manages model training, evaluation, and persistence

**Key Files**:
- `app/services/ml_service.py` - Core ML operations
- `app/services/ml_server_client.py` - External ML server integration
- `app/models/experiment.py` - Experiment tracking

**Features**:
- Project structure creation (`data/`, `models/`, `notebooks/`, `scripts/`)
- Model training execution in isolated environments
- Model persistence (pickle/joblib)
- Experiment tracking with metrics

### 3. Project Management

**Purpose**: Organizes ML projects with isolated environments

**Key Files**:
- `app/models/project.py` - Project model
- `app/services/environment_manager.py` - Virtual environment management
- `app/services/project_context.py` - Project variable context

**Project Structure**:
```
project_{id}/
├── data/           # Datasets
├── models/         # Trained models (.pkl)
├── notebooks/      # Jupyter notebooks
└── scripts/        # Generated/uploaded Python scripts
```

**Environment Management**:
- Each project links to a virtual environment
- Environments managed via `EnvironmentManager`
- Python executable path: `{env_path}/Scripts/python.exe` (Windows) or `{env_path}/bin/python` (Unix)

### 4. Experiment Tracking

**Purpose**: Tracks ML experiments with metrics and results

**Key Files**:
- `app/models/experiment.py` - Experiment model
- `app/services/metrics_parser.py` - Parses training output for metrics

**Experiment Lifecycle**:
1. User creates experiment from workflow
2. Code generated and saved to project
3. Experiment executed in project environment
4. Output captured and parsed for metrics
5. Results stored in database

### 5. Industry Modules

**Purpose**: Provides industry-specific ML nodes and scenarios

**Key Files**:
- `app/industry_modules/` - Industry-specific node definitions
- `app/models/industry_scenario.py` - Scenario definitions
- `app/services/industry_scenarios_service.py` - Scenario management

**Supported Industries**:
- Petroleum/Oil & Gas
- Finance
- Healthcare (planned)

**Industry Nodes**:
- Industry-specific data loaders
- Domain-specific preprocessing
- Industry-aware model templates

### 6. Community Integration

**Purpose**: Publishes projects to Community platform for competitions

**Key Files**:
- `app/services/community_client.py` - Community API client
- `app/services/community_connection_service.py` - Connection management

**Integration Flow**:
1. User clicks "Publish to Community"
2. Project metadata sent to Community API
3. If challenge selected, creates submission
4. Community evaluates and ranks submission

**Configuration**:
- Connection configurable via config file (planned)
- Admin can embed Community URL in app
- Supports both manual and automatic connection

## Data Flow: ML Workflow Execution

```
┌─────────────┐
│   User      │
│  Creates    │
│  Workflow   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Workflow Model │
│  (JSON stored)  │
└──────┬──────────┘
       │
       ▼
┌──────────────────────┐
│  WorkflowService     │
│  - Validates         │
│  - Topological Sort  │
│  - Generates Code    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Generated Python    │
│  Code (saved to      │
│  project/scripts/)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  MLService           │
│  - Executes in       │
│    project env       │
│  - Captures output   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  MetricsParser       │
│  - Extracts metrics  │
│  - Parses results    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Experiment Model    │
│  (Results stored)    │
└──────────────────────┘
```

## Code Generation Process

### Step 1: Workflow Validation
```python
executor = WorkflowExecutor(workflow_data)
is_valid, errors = executor.validate_workflow()
```

### Step 2: Execution Order
```python
execution_order = executor.topological_sort()
# Returns: ['node_1', 'node_2', 'node_3', ...]
```

### Step 3: Code Generation
```python
code = workflow_service.generate_code_from_workflow(
    workflow_data, 
    framework='scikit-learn',
    project_id=project_id
)
```

### Step 4: Variable Management
- Each node gets a variable name based on its type
- Variables passed between nodes via edges
- Project context provides standard variable names (X, y, model, etc.)

## Database Schema

### Core Tables

**ml_projects**
- `id`, `name`, `description`, `template`
- `environment_name` (links to virtual env)
- `framework`, `python_version`
- `industry_profile`, `scenario_id`
- `competition_id` (links to Community)

**workflows**
- `id`, `project_id`, `name`, `description`
- `workflow_data` (JSON)
- `generated_code` (Python code)
- `status` (draft, saved, executed)

**experiments**
- `id`, `project_id`, `workflow_id`
- `name`, `description`
- `script_path`, `status`
- `metrics` (JSON)
- `results` (JSON)

## API Endpoints

### Projects
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Workflows
- `GET /projects/{id}/workflows` - List workflows
- `POST /projects/{id}/workflows` - Create workflow
- `GET /workflows/{id}` - Get workflow
- `PUT /workflows/{id}` - Update workflow
- `POST /workflows/{id}/generate-code` - Generate code
- `POST /workflows/{id}/execute` - Execute workflow

### Experiments
- `GET /experiments` - List experiments
- `POST /experiments` - Create experiment
- `GET /experiments/{id}` - Get experiment
- `POST /experiments/{id}/run` - Run experiment

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-SocketIO
- **Frontend**: React, ReactFlow (for visual workflows)
- **ML**: scikit-learn, TensorFlow, XGBoost (framework support)
- **Database**: SQLite (dev), PostgreSQL (production)
- **Environment**: Embedded Python 3.11.7, virtualenv

## Key Design Patterns

1. **Application Factory**: Flask app created via `create_app()`
2. **Service Layer**: Business logic in services, not routes
3. **Dependency Injection**: Services receive dependencies via constructor
4. **Repository Pattern**: Models abstract database access
5. **Strategy Pattern**: Different code generators for different frameworks

## Security Considerations

- JWT authentication for API access
- Project isolation via separate environments
- Input validation on workflow data
- Code execution in sandboxed environments
- Rate limiting on API endpoints

## Performance Optimizations

- Lazy loading of workflow data
- Caching of generated code
- Async execution for long-running experiments
- WebSocket for real-time updates
- Database indexing on frequently queried fields

## Future Enhancements

- Multi-user collaboration on workflows
- Version control for workflows
- Model registry and deployment
- Automated hyperparameter tuning
- Integration with MLflow
- Support for more ML frameworks (PyTorch, etc.)

