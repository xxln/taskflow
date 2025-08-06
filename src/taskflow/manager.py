"""
Core business logic for the simplified task management system.

This module provides the main TaskManager class that coordinates between
the data models and storage layer to provide high-level task management
operations.
"""

from typing import List, Dict, Any, Tuple

from .models import (
    Project, Task, Iteration, TaskStatus, ProjectStatus, IterationStatus
)
from .storage import TaskStorage


class TaskManagerError(Exception):
    """Base exception for task manager operations."""
    pass


class ProjectNotFoundError(TaskManagerError):
    """Raised when a project is not found."""
    pass


class TaskNotFoundError(TaskManagerError):
    """Raised when a task is not found."""
    pass


class IterationNotFoundError(TaskManagerError):
    """Raised when an iteration is not found."""
    pass


class TaskManager:
    """Main task management coordinator class."""
    
    def __init__(self, base_dir: str = "projects"):
        """Initialize task manager with storage backend."""
        self.storage = TaskStorage(base_dir)
    
    # Project management
    
    def create_project(self, name: str, description: str = "") -> Project:
        """Create a new project."""
        if self.storage.project_exists(name):
            raise TaskManagerError(f"Project '{name}' already exists")
        
        # Create directory structure
        self.storage.create_project_directory(name)
        
        # Create project metadata
        project = Project(name=name, description=description)
        self.storage.save_project(project)
        
        return project
    
    def get_project(self, name: str) -> Project:
        """Get project by name."""
        project = self.storage.load_project(name)
        if not project:
            raise ProjectNotFoundError(f"Project '{name}' not found")
        return project
    
    def list_projects(self) -> List[str]:
        """List all project names."""
        return self.storage.list_projects()
    
    def set_project_status(self, name: str, status: str) -> None:
        """Set project status."""
        project = self.get_project(name)
        
        try:
            project.status = ProjectStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in ProjectStatus]
            raise TaskManagerError(
                f"Invalid status '{status}'. Valid options: {valid_statuses}"
            )
        
        self.storage.save_project(project)
    
    def get_project_status(self, name: str) -> Dict[str, Any]:
        """Get project status and statistics."""
        if not self.storage.project_exists(name):
            return {"exists": False}
        
        return self.storage.get_project_stats(name)
    
    # Task management
    
    def create_task(
        self, project_name: str, title: str, description: str = "", 
        notes: str = ""
    ) -> Task:
        """Create a new task in a project."""
        project = self.get_project(project_name)
        
        # Get next task ID and update project
        task_id = project.get_next_task_id()
        self.storage.save_project(project)
        
        # Create task
        task = Task(
            id=task_id,
            title=title,
            project=project_name,
            description=description,
            notes=notes
        )
        
        self.storage.save_task(task)
        return task
    
    def get_task(self, project_name: str, task_id: str) -> Task:
        """Get task by project and ID."""
        if not self.storage.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")
        
        task = self.storage.load_task(project_name, task_id)
        if not task:
            raise TaskNotFoundError(
                f"Task '{task_id}' not found in project '{project_name}'"
            )
        
        return task
    
    def list_tasks(self, project_name: str) -> List[str]:
        """List all task IDs in a project."""
        if not self.storage.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")
        
        return self.storage.list_tasks(project_name)
    
    def set_task_status(self, project_name: str, task_id: str, status: str) -> None:
        """Set task status."""
        task = self.get_task(project_name, task_id)
        
        try:
            new_status = TaskStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in TaskStatus]
            raise TaskManagerError(
                f"Invalid status '{status}'. Valid options: {valid_statuses}"
            )
        
        # Handle status transitions
        if new_status == TaskStatus.IN_PROGRESS and task.started is None:
            task.start_work()
        elif new_status == TaskStatus.DONE and task.completed is None:
            task.complete_work()
            # Update project completed tasks counter
            project = self.get_project(project_name)
            project.mark_task_completed()
            self.storage.save_project(project)
        else:
            task.status = new_status
        
        self.storage.save_task(task)
    
    def start_task(self, project_name: str, task_id: str) -> Iteration:
        """Start working on a task by creating first iteration."""
        task = self.get_task(project_name, task_id)
        
        # Start the task if not already started
        if task.status == TaskStatus.TODO:
            task.start_work()
            self.storage.save_task(task)
        
        # Create first iteration
        iteration_num = self.storage.get_next_iteration_number(project_name, task_id)
        iteration = Iteration(
            task_id=task_id,
            iteration=iteration_num
        )
        
        # Update task iteration counters
        task.current_iteration = iteration_num
        task.total_iterations = max(task.total_iterations, iteration_num)
        self.storage.save_task(task)
        
        # Save iteration
        self.storage.save_iteration(iteration, project_name)
        
        return iteration
    
    def complete_task(self, project_name: str, task_id: str) -> None:
        """Complete a task."""
        task = self.get_task(project_name, task_id)
        
        # Complete current iteration if exists
        current_iter = self.storage.get_current_iteration(project_name, task_id)
        if current_iter and current_iter.status != IterationStatus.COMPLETED:
            current_iter.complete()
            self.storage.save_iteration(current_iter, project_name)
        
        # Complete the task
        if task.status != TaskStatus.DONE:
            task.complete_work()
            self.storage.save_task(task)
            
            # Update project stats
            project = self.get_project(project_name)
            project.mark_task_completed()
            self.storage.save_project(project)
    
    # Iteration management
    
    def get_iteration(self, project_name: str, task_id: str, iteration_num: int) -> Iteration:
        """Get specific iteration."""
        if not self.storage.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")
        
        iteration = self.storage.load_iteration(project_name, task_id, iteration_num)
        if not iteration:
            raise IterationNotFoundError(
                f"Iteration {iteration_num} not found for task '{task_id}' in project '{project_name}'"
            )
        
        return iteration
    
    def list_iterations(self, project_name: str, task_id: str) -> List[int]:
        """List all iteration numbers for a task."""
        # Verify task exists
        self.get_task(project_name, task_id)
        return self.storage.list_iterations(project_name, task_id)
    
    def add_iteration_note(self, project_name: str, task_id: str, note: str) -> None:
        """Add a note to the current iteration."""
        current_iter = self.storage.get_current_iteration(project_name, task_id)
        if not current_iter:
            raise IterationNotFoundError(f"No active iteration found for task '{task_id}'")
        
        current_iter.add_note(note)
        self.storage.save_iteration(current_iter, project_name)
    
    def set_iteration_summary(self, project_name: str, task_id: str, summary: str) -> None:
        """Set summary for current iteration."""
        current_iter = self.storage.get_current_iteration(project_name, task_id)
        if not current_iter:
            raise IterationNotFoundError(f"No active iteration found for task '{task_id}'")
        
        current_iter.summary = summary
        self.storage.save_iteration(current_iter, project_name)
    
    def add_user_feedback(self, project_name: str, task_id: str, feedback: str) -> None:
        """Add user feedback to current iteration."""
        current_iter = self.storage.get_current_iteration(project_name, task_id)
        if not current_iter:
            raise IterationNotFoundError(f"No active iteration found for task '{task_id}'")
        
        current_iter.user_feedback = feedback
        self.storage.save_iteration(current_iter, project_name)
    
    def set_next_steps(self, project_name: str, task_id: str, next_steps: str) -> None:
        """Set next steps for current iteration."""
        current_iter = self.storage.get_current_iteration(project_name, task_id)
        if not current_iter:
            raise IterationNotFoundError(f"No active iteration found for task '{task_id}'")
        
        current_iter.next_steps = next_steps
        self.storage.save_iteration(current_iter, project_name)
    
    def complete_iteration(self, project_name: str, task_id: str) -> None:
        """Complete the current iteration."""
        current_iter = self.storage.get_current_iteration(project_name, task_id)
        if not current_iter:
            raise IterationNotFoundError(f"No active iteration found for task '{task_id}'")
        
        current_iter.complete()
        self.storage.save_iteration(current_iter, project_name)
    
    # Utility methods
    
    def get_task_details(self, project_name: str, task_id: str) -> Dict[str, Any]:
        """Get comprehensive task details including iterations."""
        task = self.get_task(project_name, task_id)
        iterations = self.list_iterations(project_name, task_id)
        
        return {
            "task": task.to_dict(),
            "iteration_count": len(iterations),
            "iterations": iterations,
            "current_iteration": self.storage.get_current_iteration(project_name, task_id)
        }
    
    def search_tasks(self, project_name: str, query: str) -> List[Tuple[str, str]]:
        """Search tasks by title or description."""
        task_ids = self.list_tasks(project_name)
        results = []
        
        query_lower = query.lower()
        for task_id in task_ids:
            task = self.storage.load_task(project_name, task_id)
            if task:
                if (query_lower in task.title.lower() or 
                    query_lower in task.description.lower()):
                    results.append((task_id, task.title))
        
        return results
    
    def cleanup(self) -> None:
        """Clean up empty directories and orphaned files."""
        self.storage.cleanup_empty_directories()