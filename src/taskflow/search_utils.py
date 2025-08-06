"""
Search and filtering utilities for the task management system.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .models import Task, TaskStatus, Iteration
from .storage import TaskStorage

class TaskSearchEngine:
    """Advanced search capabilities for tasks and iterations."""
    
    def __init__(self, storage: TaskStorage):
        self.storage = storage
    
    def search_across_projects(self, query: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for tasks across all projects."""
        results = []
        query_lower = query.lower()
        
        for project_name in self.storage.list_projects():
            for task_id in self.storage.list_tasks(project_name):
                task = self.storage.load_task(project_name, task_id)
                if task:
                    # Check if query matches
                    if (query_lower in task.title.lower() or 
                        query_lower in task.description.lower() or
                        query_lower in task.notes.lower()):
                        
                        # Apply status filter if provided
                        if status_filter and task.status.value != status_filter:
                            continue
                        
                        results.append({
                            'project': project_name,
                            'task_id': task.id,
                            'title': task.title,
                            'status': task.status.value,
                            'match_context': self._get_match_context(task, query_lower)
                        })
        
        return results
    
    def search_iterations(self, project_name: str, task_id: str, query: str) -> List[Dict[str, Any]]:
        """Search within task iterations."""
        results = []
        query_lower = query.lower()
        
        for iter_num in self.storage.list_iterations(project_name, task_id):
            iteration = self.storage.load_iteration(project_name, task_id, iter_num)
            if iteration:
                # Check all iteration fields
                if (query_lower in iteration.notes.lower() or
                    query_lower in iteration.summary.lower() or
                    query_lower in iteration.user_feedback.lower() or
                    query_lower in iteration.next_steps.lower()):
                    
                    results.append({
                        'iteration': iter_num,
                        'status': iteration.status.value,
                        'match_context': self._get_iteration_match_context(iteration, query_lower)
                    })
        
        return results
    
    def find_related_tasks(self, project_name: str, task_id: str) -> List[Dict[str, Any]]:
        """Find tasks that might be related based on content similarity."""
        source_task = self.storage.load_task(project_name, task_id)
        if not source_task:
            return []
        
        # Extract keywords from source task
        keywords = self._extract_keywords(source_task)
        related = []
        
        for tid in self.storage.list_tasks(project_name):
            if tid == task_id:
                continue
                
            task = self.storage.load_task(project_name, tid)
            if task:
                similarity_score = self._calculate_similarity(keywords, task)
                if similarity_score > 0.3:  # Threshold for relevance
                    related.append({
                        'task_id': task.id,
                        'title': task.title,
                        'similarity': similarity_score
                    })
        
        return sorted(related, key=lambda x: x['similarity'], reverse=True)
    
    def get_recent_activity(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recently updated tasks across all projects."""
        recent = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for project_name in self.storage.list_projects():
            for task_id in self.storage.list_tasks(project_name):
                task = self.storage.load_task(project_name, task_id)
                if task:
                    # Check if task was updated recently
                    last_update = self._get_last_update(task)
                    if last_update and last_update > cutoff:
                        recent.append({
                            'project': project_name,
                            'task_id': task.id,
                            'title': task.title,
                            'last_update': last_update.isoformat()
                        })
        
        return sorted(recent, key=lambda x: x['last_update'], reverse=True)
    
    def _get_match_context(self, task: Task, query: str) -> str:
        """Get context around the match in task."""
        for field in [task.title, task.description, task.notes]:
            if query in field.lower():
                idx = field.lower().index(query)
                start = max(0, idx - 30)
                end = min(len(field), idx + len(query) + 30)
                return f"...{field[start:end]}..."
        return ""
    
    def _get_iteration_match_context(self, iteration: Iteration, query: str) -> str:
        """Get context around the match in iteration."""
        for field in [iteration.notes, iteration.summary, iteration.user_feedback, iteration.next_steps]:
            if query in field.lower():
                idx = field.lower().index(query)
                start = max(0, idx - 30)
                end = min(len(field), idx + len(query) + 30)
                return f"...{field[start:end]}..."
        return ""
    
    def _extract_keywords(self, task: Task) -> List[str]:
        """Extract keywords from task for similarity matching."""
        import re
        text = f"{task.title} {task.description} {task.notes}"
        # Extract words longer than 3 characters, excluding common words
        words = re.findall(r'\b\w{4,}\b', text.lower())
        common_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'what', 'when', 'where'}
        return [w for w in words if w not in common_words]
    
    def _calculate_similarity(self, keywords: List[str], task: Task) -> float:
        """Calculate similarity score between keywords and task."""
        task_text = f"{task.title} {task.description} {task.notes}".lower()
        matches = sum(1 for kw in keywords if kw in task_text)
        return matches / len(keywords) if keywords else 0
    
    def _get_last_update(self, task: Task) -> Optional[datetime]:
        """Get the last update time for a task."""
        dates = []
        
        # Parse task dates
        for date_str in [task.created, task.started, task.completed]:
            if date_str:
                try:
                    dates.append(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
                except:
                    pass
        
        return max(dates) if dates else None


class TaskFilter:
    """Filter tasks based on various criteria."""
    
    @staticmethod
    def filter_by_status(tasks: List[Task], status: TaskStatus) -> List[Task]:
        """Filter tasks by status."""
        return [t for t in tasks if t.status == status]
    
    @staticmethod
    def filter_by_project(tasks: List[Task], project: str) -> List[Task]:
        """Filter tasks by project."""
        return [t for t in tasks if t.project == project]
    
    @staticmethod
    def filter_by_date_range(tasks: List[Task], start_date: datetime, end_date: datetime) -> List[Task]:
        """Filter tasks by date range."""
        filtered = []
        for task in tasks:
            if task.created:
                try:
                    created_date = datetime.fromisoformat(task.created.replace('Z', '+00:00'))
                    if start_date <= created_date <= end_date:
                        filtered.append(task)
                except:
                    pass
        return filtered
    
    @staticmethod
    def filter_incomplete(tasks: List[Task]) -> List[Task]:
        """Get incomplete tasks."""
        return [t for t in tasks if t.status not in [TaskStatus.DONE, TaskStatus.ARCHIVED]]
