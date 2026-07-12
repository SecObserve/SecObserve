# AGENTS.md

## Project Overview
SecObserve is an open-source vulnerability management system designed for software development and cloud environments. It aggregates security findings from various tools and provides a centralized platform for managing, analyzing, and tracking vulnerabilities.

## Backend

### Tech stack

- **Backend**: Python 3.12+, Django 6, Django REST Framework
- **Database**: Supports MySQL (via `pymysql`) and PostgreSQL (via `psycopg`)
- **Task Queue**: Huey
- **API Documentation**: OpenAPI 3 (via `drf-spectacular`)
- **Web Server**: Gunicorn
- **Package Management**: Poetry

### Structure

- `backend.application`:
   - `access_control`: Manages users, API tokens and authorization.
   - `authorization`: Implements RBAC (roles and permissions).
   - `background_tasks`: Functionality for tasks running in the background.
   - `commons`: Cross-cutting functions and data, including settings.
   - `constance`: Unused, is needed for a transition.
   - `core`: Core functionality around products and their observations.
   - `epss`: Enrichment of observations with Exploit Prediction Scoring System (EPSS) and exploitation data.
   - `import_observations`: Handles importing security observations from various parsers (e.g., Trivy, Snyk, ZAP, etc.).
   - `issue_tracker`: Integrates with external issue trackers (e.g., Jira, GitHub, GitLab).
   - `licenses`: Manages and tracks software licenses.
   - `metrics`: Provides metrics about observations and licenses.
   - `notifications`: Sends notifications to Slack, MS Teams and email for various events.
   - `rules`: Implements rules to automatically amend status, severity and priority of observations.
   - `vex`: Import and export of Vulnerability Exploitability eXchange (VEX) information.
- `backend.config`: Configurations
- `backend.templates`: Fixed content

### Unit tests

- Stored under `backend.unittests` with same structure as `application`
- Test classes derived from `unittests.base_test_case.BaseTestCase`
- Use `@patch` annotation for mocks

### Development Workflow

### Prerequisites

- Python 3.12+
- Poetry for dependency management

#### Setup and Running

- **Install dependencies**:

   ```bash
   poetry install
   ```
- **Start development server** (including frontend):

  ```bash
  ./bin/dev.sh
  ```

#### Testing

- **Unit tests**:
  ```bash
  ./bin/unittests.sh
  ```
- **Code Quality**:
  ```bash
  cd backend

  # Formatting
  black .
  isort.

  # Linting
  flake8
  ./bin/run_pylint.sh

  # Type Checking
  ./bin/run_mypy.sh
  ```

### Key Patterns

- **Service Layer**: Business logic should reside in `application.<app_name>.services`.
- **API Layer**: REST endpoints are defined in `application.<app_name>.api`.
- **Query Layer**: Database queries are abstracted in `application.<app_name>.queries`.
- **Parsers**: Import logic for external tools is located in `application.import_observations.parsers`.

### Coding Standards

- **Line Length**: 120 characters (configured via `black`).
- **Type Hinting**: Strongly encouraged throughout the codebase.
- **Documentation**: Use docstrings for complex logic; otherwise, keep code self-documenting with clear identifiers.

## Frontend

### Tech Stack
- **Framework**: React 19 with TypeScript
- **UI Library**: Material-UI 7 with ECharts integration
- **Admin Panel**: react-admin 5 (CRUD interfaces for data management)
- **Build Tool**: Vite
- **Styling**: Emotion (CSS-in-JS)
- **Charts**: Chart.js with react-chartjs-2
- **Markdown**: MDXEditor, marked, markdown-to-jsx
- **Diagrams**: Mermaid
- **Authentication**: OIDC (via `react-oidc-context` and `oidc-client-ts`)
- **Package Management**: npm

### Structure
- `frontend/src/`:
   - `access_control`: Manages users, API tokens and authorization.
   - `background_tasks`: Functionality for tasks running in the background.
   - `commons/`: Shared components, layout, and utilities
     - `layout/`: Main Layout, SubMenu, ListHeader
     - `custom_fields/`: Reusable field components
     - `settings/`: Application settings UI
   - `core`: Core functionality around products and their observations.
   - `dashboard`: Dashboard showing different metrics.
   - `import_observations`: Handles importing security observations from various parsers (e.g., Trivy, Snyk, ZAP, etc.).
   - `licenses`: Manages and tracks software licenses.
   - `metrics`: Provides metrics about observations and licenses.
   - `notifications`: Sends notifications to Slack, MS Teams and email for various events.
   - `rules`: Implements rules to automatically amend status, severity and priority of observations.
   - `types`: Declaration of environment variables.
   - `vex`: Import and export of Vulnerability Exploitability eXchange (VEX) information.

### Key Patterns
- **Pages**: List, Show, Create, and Edit components for each entity (aligned with react-admin patterns).
- **Runtime Config**: `runtime-env-cra` library injects environment variables at build time.

### Development Workflow

#### Prerequisites
- Node.js (compatible with Vite 8)

#### Setup and Running
1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```
2. **Start development server**:
   ```bash
   npm start
   ```
3. **Build for production**:
   ```bash
   npm run build
   ```

#### Code Quality
```bash
# Linting
npm run lint

# Formatting and import sorting (Prettier)
prettier -w src
```

### Coding Standards
- **Line Length**: 120 characters (configured via `.prettierrc.json`).
- **TypeScript**: Strict mode enabled; all components should be fully typed.
- **Component Style**: Functional components with hooks; no class components.
