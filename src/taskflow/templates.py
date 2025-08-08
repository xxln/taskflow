"""
Task templates for common patterns.
"""

from typing import Dict, Any
from pathlib import Path
import json

class TaskTemplates:
    """Manage task templates for common patterns."""
    
    DEFAULT_TEMPLATES = {
        'bug_investigation': {
            'title': 'Investigate: {issue_description}',
            'description': '''## Issue Report
            
### Observed Behavior
* {observed}

### Expected Behavior  
* {expected}

### Reproduction Steps
1. {step1}
2. {step2}

### Environment
* Configuration: {config_file}
* Version: {version}
''',
            'notes': '''## Investigation Log

### Initial Analysis
- [ ] Review relevant source files
- [ ] Check recent changes
- [ ] Test with minimal configuration

### Root Cause Analysis
- [ ] Identify failing component
- [ ] Trace execution flow
- [ ] Verify assumptions

### Solution Approach
- [ ] Design fix
- [ ] Consider edge cases
- [ ] Plan testing strategy
'''
        },
        
        'feature_implementation': {
            'title': 'Implement: {feature_name}',
            'description': '''## Feature Specification

### Overview
{feature_overview}

### Requirements
* {requirement1}
* {requirement2}

### Acceptance Criteria
- [ ] {criteria1}
- [ ] {criteria2}

### Technical Design
* Components affected: {components}
* Dependencies: {dependencies}
''',
            'notes': '''## Implementation Progress

### Phase 1: Design
- [ ] Review requirements
- [ ] Create technical design
- [ ] Identify risks

### Phase 2: Development
- [ ] Implement core functionality
- [ ] Add error handling
- [ ] Write tests

### Phase 3: Integration
- [ ] Integration testing
- [ ] Documentation
- [ ] Code review
'''
        },
        
        'refactoring': {
            'title': 'Refactor: {component_name}',
            'description': '''## Refactoring Plan

### Current Issues
* {issue1}
* {issue2}

### Proposed Changes
* {change1}
* {change2}

### Impact Analysis
* Files affected: {files}
* Tests to update: {tests}
* Backward compatibility: {compatibility}
''',
            'notes': '''## Refactoring Checklist

### Pre-refactoring
- [ ] Ensure tests pass
- [ ] Document current behavior
- [ ] Create safety branch

### During Refactoring
- [ ] Make incremental changes
- [ ] Run tests frequently
- [ ] Maintain functionality

### Post-refactoring
- [ ] All tests pass
- [ ] Performance verified
- [ ] Documentation updated
'''
        },
        
        'optimization': {
            'title': 'Optimize: {performance_issue}',
            'description': '''## Performance Optimization

### Performance Issue
* Metric: {metric}
* Current: {current_value}
* Target: {target_value}

### Profiling Results
* Bottleneck: {bottleneck}
* Impact: {impact}
''',
            'notes': '''## Optimization Strategy

### Analysis
- [ ] Profile current implementation
- [ ] Identify hotspots
- [ ] Measure baseline

### Implementation
- [ ] Apply optimization
- [ ] Verify correctness
- [ ] Measure improvement

### Validation
- [ ] Performance tests
- [ ] Regression tests
- [ ] Document results
'''
        }
    }
    
    def __init__(self, template_dir: str = "tasks/templates"):
        """Initialize template manager.

        Note: We no longer auto-create the template directory to avoid
        creating an empty top-level `tasks/` folder. The directory will be
        created on-demand when saving a custom template.
        """
        self.template_dir = Path(template_dir)
        self.templates = self.DEFAULT_TEMPLATES.copy()
        self._load_custom_templates()
    
    def _load_custom_templates(self):
        """Load custom templates from template directory if it exists."""
        if not self.template_dir.exists():
            return
        for template_file in self.template_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    template_name = template_file.stem
                    self.templates[template_name] = template_data
            except Exception:
                pass
    
    def get_template(self, template_name: str) -> Dict[str, str]:
        """Get a template by name."""
        return self.templates.get(template_name, self.DEFAULT_TEMPLATES['bug_investigation'])
    
    def list_templates(self) -> list:
        """List available template names."""
        return list(self.templates.keys())
    
    def save_custom_template(self, name: str, template: Dict[str, str]):
        """Save a custom template (creates directory on demand)."""
        self.template_dir.mkdir(parents=True, exist_ok=True)
        template_file = self.template_dir / f"{name}.json"
        with open(template_file, 'w') as f:
            json.dump(template, f, indent=2)
        self.templates[name] = template
    
    def apply_template(self, template_name: str, variables: Dict[str, str]) -> Dict[str, str]:
        """Apply a template with variable substitution."""
        template = self.get_template(template_name)
        result = {}
        
        for field, content in template.items():
            # Simple variable substitution
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                content = content.replace(placeholder, var_value)
            result[field] = content
        
        return result


class TaskConfig:
    """User configuration for the task management system."""
    
    DEFAULT_CONFIG = {
        'default_project': None,
        'editor': 'nano',
        'date_format': '%Y-%m-%d %H:%M',
        'auto_start_iteration': True,
        'show_completed_tasks': False,
        'task_id_format': '{number:03d}',
        'max_title_length': 50,
        'shortcuts': {
            'ls': 'list-tasks',
            'new': 'create-task',
            'done': 'complete-task',
            'note': 'add-iteration-note',
        }
    }
    
    def __init__(self, config_file: str = "~/.tasks.config"):
        """Initialize configuration."""
        self.config_file = Path(config_file).expanduser()
        self.config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except Exception:
                pass
    
    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self.save_config()
