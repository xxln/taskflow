# Enhanced Task Management System

A powerful, lightweight task management system for local development workflows with advanced features like search, templates, and batch operations.

## 🚀 Quick Start

```bash
# Use wrapper script (recommended)
./task list-projects

# Or use Python directly
python main.py list-projects

# Enhanced commands auto-detected
./task search "COP curve"
./task quick "project" "001" -n "Progress update" -s "Fixed issue"
```

## ✨ Features

- **Project-based organization** with YAML/JSON storage
- **Iteration tracking** for complex tasks
- **Advanced search** across projects and iterations
- **Task templates** for common patterns
- **Quick batch operations** with shortcuts
- **Git-friendly** human-readable files
- **Zero dependencies** (uses standard library only)

## 📋 Core Commands

### Project Management
```bash
# Create project
./task create-project "web-app" -d "New web application"

# List all projects
./task list-projects

# Project status overview
./task status "web-app"
```

### Task Management
```bash
# Create task
./task create-task "web-app" "Setup authentication" -d "Implement user login"

# List tasks
./task list-tasks "web-app"

# Show task details
./task show-task "web-app" "001"

# Start working on task
./task start-task "web-app" "001"

# Complete task
./task complete-task "web-app" "001"
```

### Iteration Management
```bash
# Add progress notes
./task add-iteration-note "web-app" "001" "Implemented JWT tokens"

# Set summary
./task set-iteration-summary "web-app" "001" "Authentication working"

# Add user feedback
./task add-user-feedback "web-app" "001" "Consider password reset"

# Set next steps
./task set-next-steps "web-app" "001" "Add unit tests"

# Complete iteration
./task complete-iteration "web-app" "001"
```

## 🔥 Enhanced Features

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
./task search "heat pump"

# Filter by status
./task search "optimization" -s "IN_PROGRESS"
```

### Template System
```bash
# List available templates
./task templates

# Create from template
./task new-from-template "project" "bug_investigation" \
  -v issue_description="Heat pump output limited" \
  -v config_file="config.json"
```

## 📁 File Structure

```
tasks/
├── main.py              # Enhanced entry point
├── task                 # Wrapper script
├── tasks/               # Core modules
│   ├── cli.py          # Standard CLI
│   ├── enhanced_cli.py # Enhanced CLI with shortcuts
│   ├── manager.py      # Business logic
│   ├── models.py       # Data structures
│   ├── storage.py      # File operations
│   ├── search_utils.py # Search functionality
│   └── templates.py    # Template system
└── projects/           # Project data
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

### Development Example
```bash
# 1. Start feature work
./task create-project "feature-auth" -d "Authentication system"
./task create-task "feature-auth" "Database schema" -d "User tables"

# 2. Track progress
./task start-task "feature-auth" "001"
./task add-iteration-note "feature-auth" "001" "Created migration"

# 3. Continue work
./task quick "feature-auth" "001" \
  -n "Added password hashing" \
  -s "Schema complete" \
  -x "Implement API endpoints"

# 4. Complete and review
./task complete-task "feature-auth" "001"
./task status "feature-auth"
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
./task new-from-template "ies-single-step" "bug_investigation" \
  -v issue_description="Heat pump max load ratio not working" \
  -v config_file="ies-configuration.json"

# During investigation  
./task quick "ies-single-step" "002" \
  -n "Root cause: COP curve only goes to 100%" \
  -s "Issue identified in controller.py"

# Implementation
./task continue "ies-single-step" "002" -r "Implementing fix"
./task quick "ies-single-step" "002" \
  -n "Added max_load_ratio check" \
  -s "Fix implemented and tested" \
  -x "Deploy to production"

# Completion
./task complete-task "ies-single-step" "002"
```

This enhanced system transforms simple task tracking into a comprehensive development workflow assistant while maintaining the simplicity and local-first approach of the original design.
