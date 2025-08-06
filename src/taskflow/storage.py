"""
Storage layer for the simplified task management system.

This module handles all file I/O operations for projects, tasks, and iterations.
Uses YAML for task/iteration data and JSON for project metadata.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from ruamel.yaml import YAML

from .models import Project, Task, Iteration


class TaskStorage:
    """Handles all file storage operations for the task management system."""
    
    def __init__(self, base_dir: str = "projects"):
        """Initialize storage with base directory for projects."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Configure YAML with same settings as existing codebase
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
    
    # Project operations
    
    def create_project_directory(self, project_name: str) -> Path:
        """Create project directory structure."""
        project_dir = self.base_dir / project_name
        project_dir.mkdir(exist_ok=True)
        
        tasks_dir = project_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        return project_dir
    
    def save_project(self, project: Project) -> None:
        """Save project metadata to JSON file."""
        project_dir = self.base_dir / project.name
        project_file = project_dir / "project.json"
        
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, indent=2)
    
    def load_project(self, project_name: str) -> Optional[Project]:
        """Load project metadata from JSON file."""
        project_file = self.base_dir / project_name / "project.json"
        
        if not project_file.exists():
            return None
        
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Project.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def list_projects(self) -> List[str]:
        """List all available projects."""
        if not self.base_dir.exists():
            return []
        
        projects = []
        for item in self.base_dir.iterdir():
            if item.is_dir() and (item / "project.json").exists():
                projects.append(item.name)
        
        return sorted(projects)
    
    def project_exists(self, project_name: str) -> bool:
        """Check if a project exists."""
        project_dir = self.base_dir / project_name
        return project_dir.exists() and (project_dir / "project.json").exists()
    
    # Task operations
    
    def save_task(self, task: Task) -> None:
        """Save task to YAML file."""
        project_dir = self.base_dir / task.project
        tasks_dir = project_dir / "tasks"
        task_file = tasks_dir / f"{task.id}-{self._slugify(task.title)}.yaml"
        
        with open(task_file, 'w', encoding='utf-8') as f:
            self.yaml.dump(task.to_dict(), f)
    
    def load_task(self, project_name: str, task_id: str) -> Optional[Task]:
        """Load task from YAML file by ID."""
        tasks_dir = self.base_dir / project_name / "tasks"
        
        # Find task file by ID prefix
        for task_file in tasks_dir.glob(f"{task_id}-*.yaml"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    data = self.yaml.load(f)
                if data and data.get('id') == task_id:
                    return Task.from_dict(data)
            except Exception:
                continue
        
        return None
    
    def list_tasks(self, project_name: str) -> List[str]:
        """List all task IDs in a project."""
        tasks_dir = self.base_dir / project_name / "tasks"
        
        if not tasks_dir.exists():
            return []
        
        task_ids = []
        for task_file in tasks_dir.glob("*-*.yaml"):
            # Skip iteration files
            if ".iter" in task_file.stem:
                continue
            
            # Extract task ID (everything before first dash)
            name_parts = task_file.stem.split('-', 1)
            if len(name_parts) >= 1:
                task_ids.append(name_parts[0])
        
        return sorted(task_ids)
    
    def get_task_filename(self, project_name: str, task_id: str) -> Optional[str]:
        """Get the filename for a task by ID."""
        tasks_dir = self.base_dir / project_name / "tasks"
        
        for task_file in tasks_dir.glob(f"{task_id}-*.yaml"):
            if not ".iter" in task_file.stem:
                return task_file.name
        
        return None
    
    # Iteration operations
    
    def save_iteration(self, iteration: Iteration, project_name: str) -> None:
        """Save iteration to YAML file."""
        tasks_dir = self.base_dir / project_name / "tasks"
        iter_file = tasks_dir / f"{iteration.task_id}.iter{iteration.iteration:03d}.yaml"
        
        with open(iter_file, 'w', encoding='utf-8') as f:
            self.yaml.dump(iteration.to_dict(), f)
    
    def load_iteration(self, project_name: str, task_id: str, iteration_num: int) -> Optional[Iteration]:
        """Load specific iteration from YAML file."""
        tasks_dir = self.base_dir / project_name / "tasks"
        iter_file = tasks_dir / f"{task_id}.iter{iteration_num:03d}.yaml"
        
        if not iter_file.exists():
            return None
        
        try:
            with open(iter_file, 'r', encoding='utf-8') as f:
                data = self.yaml.load(f)
            return Iteration.from_dict(data)
        except Exception:
            return None
    
    def list_iterations(self, project_name: str, task_id: str) -> List[int]:
        """List all iteration numbers for a task."""
        tasks_dir = self.base_dir / project_name / "tasks"
        
        if not tasks_dir.exists():
            return []
        
        iterations = []
        for iter_file in tasks_dir.glob(f"{task_id}.iter*.yaml"):
            # Extract iteration number from filename
            stem = iter_file.stem
            if ".iter" in stem:
                iter_part = stem.split(".iter")[-1]
                try:
                    iter_num = int(iter_part)
                    iterations.append(iter_num)
                except ValueError:
                    continue
        
        return sorted(iterations)
    
    def get_next_iteration_number(self, project_name: str, task_id: str) -> int:
        """Get the next available iteration number for a task."""
        existing_iterations = self.list_iterations(project_name, task_id)
        if not existing_iterations:
            return 1
        return max(existing_iterations) + 1
    
    def get_current_iteration(self, project_name: str, task_id: str) -> Optional[Iteration]:
        """Get the most recent iteration for a task."""
        iterations = self.list_iterations(project_name, task_id)
        if not iterations:
            return None
        
        latest_iter_num = max(iterations)
        return self.load_iteration(project_name, task_id, latest_iter_num)
    
    # Utility methods
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        import re
        text = text.lower()
        return re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    
    def get_project_stats(self, project_name: str) -> Dict[str, Any]:
        """Get statistics for a project."""
        project = self.load_project(project_name)
        if not project:
            return {}
        
        tasks = self.list_tasks(project_name)
        completed_count = 0
        
        for task_id in tasks:
            task = self.load_task(project_name, task_id)
            if task and task.status.value == "DONE":
                completed_count += 1
        
        total_tasks = len(tasks)
        completion_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "exists": True,
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "pending_tasks": total_tasks - completed_count,
            "completion_percentage": completion_percentage
        }
    
    def cleanup_empty_directories(self) -> None:
        """Remove empty project directories."""
        if not self.base_dir.exists():
            return
        
        for project_dir in self.base_dir.iterdir():
            if project_dir.is_dir():
                try:
                    # Check if directory is empty or only contains empty subdirectories
                    has_content = False
                    for item in project_dir.rglob("*"):
                        if item.is_file():
                            has_content = True
                            break
                    
                    if not has_content:
                        # Remove empty directory
                        for empty_dir in reversed(list(project_dir.rglob("*"))):
                            if empty_dir.is_dir():
                                empty_dir.rmdir()
                        project_dir.rmdir()
                except OSError:
                    # Directory not empty or permission issues
                    pass