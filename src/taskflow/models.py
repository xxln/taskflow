"""
Data models for the simplified task management system.

This module defines the core data structures used throughout the task management system.
All models are designed to be easily serializable to/from YAML for simple persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
import json


class TaskStatus(Enum):
    """Valid task status values."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS" 
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class ProjectStatus(Enum):
    """Valid project status values."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class IterationStatus(Enum):
    """Valid iteration status values."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


@dataclass
class Task:
    """Represents a single task within a project."""
    id: str
    title: str
    project: str
    description: str = ""
    notes: str = ""
    status: TaskStatus = TaskStatus.TODO
    created: Optional[str] = None
    started: Optional[str] = None
    completed: Optional[str] = None
    current_iteration: int = 0
    total_iterations: int = 0
    
    def __post_init__(self):
        """Set creation timestamp if not provided."""
        if self.created is None:
            self.created = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Ensure status is TaskStatus enum
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for YAML serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status.value,
            'created': self.created,
            'started': self.started,
            'completed': self.completed,
            'project': self.project,
            'description': self.description,
            'notes': self.notes,
            'current_iteration': self.current_iteration,
            'total_iterations': self.total_iterations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary loaded from YAML."""
        # Handle status conversion
        status = data.get('status', 'TODO')
        if isinstance(status, str):
            status = TaskStatus(status)
        
        return cls(
            id=data['id'],
            title=data['title'],
            project=data['project'],
            description=data.get('description', ''),
            notes=data.get('notes', ''),
            status=status,
            created=data.get('created'),
            started=data.get('started'),
            completed=data.get('completed'),
            current_iteration=data.get('current_iteration', 0),
            total_iterations=data.get('total_iterations', 0)
        )

    def start_work(self) -> None:
        """Mark task as started."""
        if self.status == TaskStatus.TODO:
            self.status = TaskStatus.IN_PROGRESS
            self.started = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def complete_work(self) -> None:
        """Mark task as completed."""
        if self.status == TaskStatus.IN_PROGRESS:
            self.status = TaskStatus.DONE
            self.completed = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


@dataclass
class Iteration:
    """Represents a work iteration on a task."""
    task_id: str
    iteration: int
    status: IterationStatus = IterationStatus.IN_PROGRESS
    started: Optional[str] = None
    completed: Optional[str] = None
    notes: str = ""
    summary: str = ""
    user_feedback: str = ""
    next_steps: str = ""
    
    def __post_init__(self):
        """Set start timestamp if not provided."""
        if self.started is None:
            self.started = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Ensure status is IterationStatus enum
        if isinstance(self.status, str):
            self.status = IterationStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert iteration to dictionary for YAML serialization."""
        return {
            'task_id': self.task_id,
            'iteration': self.iteration,
            'started': self.started,
            'completed': self.completed,
            'status': self.status.value,
            'notes': self.notes,
            'summary': self.summary,
            'user_feedback': self.user_feedback,
            'next_steps': self.next_steps
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Iteration':
        """Create iteration from dictionary loaded from YAML."""
        # Handle status conversion
        status = data.get('status', 'in_progress')
        if isinstance(status, str):
            status = IterationStatus(status)
        
        return cls(
            task_id=data['task_id'],
            iteration=data['iteration'],
            status=status,
            started=data.get('started'),
            completed=data.get('completed'),
            notes=data.get('notes', ''),
            summary=data.get('summary', ''),
            user_feedback=data.get('user_feedback', ''),
            next_steps=data.get('next_steps', '')
        )

    def complete(self) -> None:
        """Mark iteration as completed."""
        self.status = IterationStatus.COMPLETED
        self.completed = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def add_note(self, note: str) -> None:
        """Add a note to the iteration."""
        if self.notes:
            self.notes += f"\n{note}"
        else:
            self.notes = note


@dataclass
class Project:
    """Represents a project containing multiple tasks."""
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    created: Optional[str] = None
    next_task_id: int = 1
    total_tasks: int = 0
    completed_tasks: int = 0
    
    def __post_init__(self):
        """Set creation timestamp if not provided."""
        if self.created is None:
            self.created = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Ensure status is ProjectStatus enum
        if isinstance(self.status, str):
            self.status = ProjectStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'created': self.created,
            'status': self.status.value,
            'description': self.description,
            'next_task_id': self.next_task_id,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create project from dictionary loaded from JSON."""
        # Handle status conversion
        status = data.get('status', 'active')
        if isinstance(status, str):
            status = ProjectStatus(status)
        
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            status=status,
            created=data.get('created'),
            next_task_id=data.get('next_task_id', 1),
            total_tasks=data.get('total_tasks', 0),
            completed_tasks=data.get('completed_tasks', 0)
        )

    def get_next_task_id(self) -> str:
        """Get the next available task ID and increment counter."""
        task_id = f"{self.next_task_id:03d}"
        self.next_task_id += 1
        self.total_tasks += 1
        return task_id

    def mark_task_completed(self) -> None:
        """Increment completed tasks counter."""
        self.completed_tasks += 1

    def completion_percentage(self) -> float:
        """Calculate project completion percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100