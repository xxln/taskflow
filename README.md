# Taskflow — Local-first Task Management (CLI + API + Minimal UI)

A powerful, lightweight task management system for local development workflows with advanced features like search, templates, and batch operations.

## 🚀 Quick Start

Using uv
```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run CLI (via wrapper or directly)
./bin/taskflow list-projects
# or
uv run taskflow list-projects

# Run API + open UI at http://127.0.0.1:8765
uv run taskflow-server
```

```bash
# New client wrapper
./bin/taskflow create-project demo
uv run taskflow-server
```

## ✨ Features

- **Project-based organization** with YAML/JSON storage
- **Iteration tracking** for complex tasks
- **Advanced search** across projects and iterations
- **Task templates** for common patterns
- **Quick batch operations** with shortcuts
- **Git-friendly** human-readable files
- **Local-first** file storage (YAML/JSON)
- **FastAPI** backend with simple REST endpoints
- **Minimal web UI** for creating/editing/logging tasks
- **AI-assisted text polishing** in the UI (titles, descriptions, notes, iteration fields) via OpenRouter
- **Customizable background styles** (Dark, Gradient, Grid, Light)

## 🌐 Web UI

### Background styles
- Use the background selector in the top bar to switch between Dark, Gradient, Grid, or Light. Your choice is saved in `localStorage`.

### AI-assisted editing
- Click the AI button in the top bar to open AI Settings.
- Paste your OpenRouter API key and pick a model from the dropdown (the list is fetched dynamically from OpenRouter). Your selections are saved locally as `aiKey` and `aiModel`.
- In task Create/Edit and Iteration modals, use “Polish ✨” buttons to improve the corresponding field using your selected model.
- Calls are made to OpenRouter’s Chat Completions API and include attribution headers per their quickstart. See: [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart).

## 📋 Core Commands

### Project Management (CLI)
```bash
# Create project
./bin/taskflow create-project "web-app" -d "New web application"

# List all projects
./bin/taskflow list-projects

# Project status overview
./bin/taskflow status "web-app"
```

### Task Management (CLI)
```bash
# Create task
./bin/taskflow create-task "web-app" "Setup authentication" -d "Implement user login"

# List tasks
./bin/taskflow list-tasks "web-app"

# Show task details
./bin/taskflow show-task "web-app" "001"

# Start working on task
./bin/taskflow start-task "web-app" "001"

# Complete task
./bin/taskflow complete-task "web-app" "001"
```

### Iteration Management (CLI)
```bash
# Add progress notes
./bin/taskflow add-iteration-note "web-app" "001" "Implemented JWT tokens"

# Set summary
./bin/taskflow set-iteration-summary "web-app" "001" "Authentication working"

# Add user feedback
./bin/taskflow add-user-feedback "web-app" "001" "Consider password reset"

# Set next steps
./bin/taskflow set-next-steps "web-app" "001" "Add unit tests"

# Complete iteration
./bin/taskflow complete-iteration "web-app" "001"
```

## 🔥 Enhanced CLI Features

### Quick Batch Updates
```bash
# Update multiple fields at once
./task quick "project" "001" \
  -n "Found root cause in controller.py" \
  -s "Issue identified and fixed" \
  -x "Test with production data"
```

### Task Continuation
```bash
# Reopen and continue completed tasks
./task continue "project" "001" -r "New issue discovered"
```

### Task Cloning
```bash
# Clone existing task as template
./task clone "project" "001" -t "Similar issue in different module"
```

### Cross-Project Search
```bash
# Search all projects
./bin/taskflow search "heat pump"

# Filter by status
./bin/taskflow search "optimization" -s "IN_PROGRESS"
```

### Template System
```bash
# List available templates
./bin/taskflow templates

# Create from template
./bin/taskflow new-from-template "project" "bug_investigation" \
  -v issue_description="Heat pump output limited" \
  -v config_file="config.json"
```

## 📁 File Structure

```
taskflow/
├── pyproject.toml           # uv project config
├── bin/taskflow             # client wrapper (cli/api)
├── web/                     # Minimal UI (static)
│   └── index.html
├── src/taskflow/
│   ├── __main__.py          # unified entrypoint (cli/api)
│   ├── server.py            # FastAPI app
│   ├── cli.py               # Standard CLI
│   ├── enhanced_cli.py      # Enhanced CLI
│   ├── manager.py           # Business logic
│   ├── models.py            # Data models
│   ├── storage.py           # File operations
│   ├── search_utils.py      # Search
│   └── templates.py         # Templates
└── projects/                # Data root (configurable)
    └── {project}/
        ├── project.json
        └── tasks/
            ├── 001-task-name.yaml
            └── 001.iter001.yaml
```

## 🎯 Task Templates

### Available Templates

1. **bug_investigation** - Structured bug tracking
2. **feature_implementation** - Feature development workflow  
3. **refactoring** - Code refactoring plans
4. **optimization** - Performance optimization tracking

### Template Variables

Templates support variable substitution:
```bash
./task new-from-template "project" "bug_investigation" \
  -v issue_description="API timeout" \
  -v observed="Request takes 30s" \
  -v expected="Response under 1s" \
  -v config_file="api_config.json"
```

## 🔍 Search Capabilities

### Search Syntax
- **Simple**: `./task search "keyword"`
- **With status**: `./task search "keyword" -s "IN_PROGRESS"`
- **Multiple words**: `./task search "heat pump COP"`

### Search Scope
- Task titles and descriptions
- Task notes and iteration content
- Cross-project search
- Context highlighting

## 📊 Data Formats

### Task File (YAML)
```yaml
id: "001"
title: "Fix authentication bug"
status: "IN_PROGRESS"
created: "2025-01-31T14:30:15Z"
project: "web-app"
description: |
  Detailed task description
notes: |
  Implementation notes
current_iteration: 1
total_iterations: 1
```

### Iteration File (YAML)
```yaml
task_id: "001"
iteration: 1
started: "2025-01-31T15:00:00Z"
status: "in_progress"
notes: |
  Progress notes
summary: |
  What was accomplished
user_feedback: |
  Feedback and suggestions
next_steps: |
  Planned actions
```

### Project File (JSON)
```json
{
  "name": "web-app",
  "created": "2025-01-31T14:00:00Z",
  "status": "active",
  "description": "Web application project",
  "next_task_id": 2,
  "total_tasks": 1,
  "completed_tasks": 0
}
```

## 🛠 Development Integration

### API Endpoints (MVP)
- GET `/projects`
- POST `/projects` { name, description? }
- GET `/projects/{project}/status`
- GET `/projects/{project}/tasks`
- POST `/projects/{project}/tasks` { title, description?, notes? }
- GET `/projects/{project}/tasks/{taskId}`
- PATCH `/projects/{project}/tasks/{taskId}` { title?, description?, notes?, status? }
- POST `/projects/{project}/tasks/{taskId}/iterations/start`
- POST `/projects/{project}/tasks/{taskId}/iterations/note` { note }
- POST `/projects/{project}/tasks/{taskId}/iterations/summary` { summary }
- GET `/projects/{project}/tasks/{taskId}/iterations/current`
- POST `/projects/{project}/tasks/{taskId}/iterations/feedback` { feedback }
- POST `/projects/{project}/tasks/{taskId}/iterations/next-steps` { next_steps }
- POST `/projects/{project}/tasks/{taskId}/iterations/complete`

### MCP Server (MVP)
- Start server: `uv run taskflow-mcp` (WebSocket on `ws://127.0.0.1:8787`)
- Message format: JSON-RPC 2.0
- Methods:
  - `mcp.getProjects`
  - `mcp.setBaseDir` { path }
  - `mcp.listTasks` { project, filters? }
  - `mcp.createTask` { project, title, description?, notes? }
  - `mcp.updateTask` { project, task_id, fields }
  - `mcp.deleteTask` { project, task_id }
  - `mcp.addNote` { project, task_id, note }
  - `mcp.startIteration` { project, task_id }
  - `mcp.completeIteration` { project, task_id }
  - `mcp.projectStatus` { project }

- Notifications:
  - `mcp.taskUpdated` { project, task_id }
  - `mcp.projectUpdated` { project }

- Example client: `uv run python -m taskflow.mcp_client_example`

### Cursor IDE Integration
- **Terminal commands**: Run from integrated terminal
- **File-based storage**: Human-readable diffs for Git
- **Local-only**: No server dependencies
- **Project context**: Mirrors development structure

### Git Workflow
```bash
# Track task files in Git
git add tasks/projects/my-project/
git commit -m "Add project tasks and progress"

# Human-readable diffs
git diff tasks/projects/my-project/tasks/001-task.yaml
```

### Development Example (CLI)
```bash
# 1. Start feature work
./bin/taskflow create-project "feature-auth" -d "Authentication system"
./bin/taskflow create-task "feature-auth" "Database schema" -d "User tables"

# 2. Track progress
./bin/taskflow start-task "feature-auth" "001"
./bin/taskflow add-iteration-note "feature-auth" "001" "Created migration"

# 3. Continue work
./bin/taskflow quick "feature-auth" "001" \
  -n "Added password hashing" \
  -s "Schema complete" \
  -x "Implement API endpoints"

# 4. Complete and review
./bin/taskflow complete-task "feature-auth" "001"
./bin/taskflow status "feature-auth"
```

## 🔧 Advanced Usage

### Custom Templates
Create custom templates in `tasks/templates/`:
```json
{
  "title": "Code Review: {pr_number}",
  "description": "Review PR #{pr_number}\nAuthor: {author}",
  "notes": "## Review Checklist\n- [ ] Code quality\n- [ ] Tests"
}
```

### Batch Operations
```bash
# Multiple quick updates
for task in 001 002 003; do
  ./task quick "project" "$task" -n "Batch update: refactored common code"
done
```

### Search and Filter
```bash
# Find incomplete tasks
./task search "" -s "IN_PROGRESS"

# Find recent work
./task search "$(date +%Y-%m-%d)"
```

## 📈 Best Practices

### Task Organization
- One task per issue/feature
- Use iterations for continuations  
- Complete iterations before starting new ones
- Add notes during work, not after

### Naming Conventions
- **Projects**: `{component}-{type}` (e.g., "auth-feature")
- **Tasks**: Action-oriented (e.g., "Fix login validation")
- **Notes**: Present tense progress updates

### Documentation
- Use markdown in descriptions
- Include code references with `@filename`
- Add configuration files to task directories
- Document decisions in iteration summaries

## 🤝 Contributing

The system is designed for extension:

1. **Add commands**: Extend `enhanced_cli.py`
2. **New templates**: Add to `templates.py` 
3. **Search features**: Enhance `search_utils.py`
4. **Data models**: Extend `models.py`

## 📝 Migration Notes

If upgrading from the basic version:
- All existing projects and tasks are preserved
- Enhanced features are backward compatible
- Use `./task` wrapper for new features
- Original `python main.py` commands still work

## 🎉 Example Workflow

Real-world development workflow:
```bash
# Investigation phase
./bin/taskflow new-from-template "ies-single-step" "bug_investigation" \
  -v issue_description="Heat pump max load ratio not working" \
  -v config_file="ies-configuration.json"

# During investigation  
./bin/taskflow quick "ies-single-step" "002" \
  -n "Root cause: COP curve only goes to 100%" \
  -s "Issue identified in controller.py"

# Implementation
./bin/taskflow continue "ies-single-step" "002" -r "Implementing fix"
uv run taskflow-enhanced quick "ies-single-step" "002" \
  -n "Added max_load_ratio check" \
  -s "Fix implemented and tested" \
  -x "Deploy to production"

# Completion
./bin/taskflow complete-task "ies-single-step" "002"
```

This enhanced system transforms simple task tracking into a comprehensive development workflow assistant while maintaining the simplicity and local-first approach of the original design.
