#!/usr/bin/env python3
"""
Simple command-line interface for the task management system.

This provides a clean CLI using only standard library components (argparse).
"""

import argparse
import sys
from typing import Optional

from .manager import (
    TaskManager, TaskManagerError, ProjectNotFoundError, 
    TaskNotFoundError, IterationNotFoundError
)


def format_table(headers: list, rows: list, max_width: int = 80) -> str:
    """Format data as a simple text table."""
    if not rows:
        return "No data to display."
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Create separator
    separator = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    
    # Format header
    header_row = "|" + "|".join(f" {headers[i]:<{widths[i]}} " for i in range(len(headers))) + "|"
    
    # Format data rows
    data_rows = []
    for row in rows:
        formatted_row = "|" + "|".join(f" {str(row[i]):<{widths[i]}} " for i in range(len(row))) + "|"
        data_rows.append(formatted_row)
    
    # Combine all parts
    result = [separator, header_row, separator]
    result.extend(data_rows)
    result.append(separator)
    
    return "\n".join(result)


class TaskCLI:
    """Command-line interface for task management."""
    
    def __init__(self):
        """Initialize CLI with task manager."""
        self.manager = TaskManager()
    
    def error(self, message: str) -> None:
        """Print error message and exit."""
        print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(1)
    
    def success(self, message: str) -> None:
        """Print success message."""
        print(f"✓ {message}")
    
    def info(self, message: str) -> None:
        """Print informational message."""
        print(message)
    
    # Project commands
    
    def create_project(self, args) -> None:
        """Create a new project."""
        try:
            project = self.manager.create_project(args.name, args.description or "")
            self.success(f"Created project '{project.name}'")
            self.info(f"Project directory: projects/{project.name}")
        except TaskManagerError as e:
            self.error(str(e))
    
    def list_projects(self, args) -> None:
        """List all projects."""
        try:
            projects = self.manager.list_projects()
            if not projects:
                self.info("No projects found.")
                return
            
            print("\nProjects:")
            for i, project_name in enumerate(projects, 1):
                status_info = self.manager.get_project_status(project_name)
                completion = status_info.get('completion_percentage', 0)
                print(f"  {i}. {project_name} ({completion:.1f}% complete)")
            
        except TaskManagerError as e:
            self.error(str(e))
    
    def set_project_status(self, args) -> None:
        """Set project status."""
        try:
            self.manager.set_project_status(args.name, args.status)
            self.success(f"Set project '{args.name}' status to '{args.status}'")
        except TaskManagerError as e:
            self.error(str(e))
    
    # Task commands
    
    def create_task(self, args) -> None:
        """Create a new task."""
        try:
            task = self.manager.create_task(
                args.project, 
                args.title, 
                args.description or "", 
                args.notes or ""
            )
            self.success(f"Created task {task.id}: '{task.title}' in project '{args.project}'")
        except TaskManagerError as e:
            self.error(str(e))
    
    def list_tasks(self, args) -> None:
        """List tasks in a project."""
        try:
            task_ids = self.manager.list_tasks(args.project)
            if not task_ids:
                self.info(f"No tasks found in project '{args.project}'.")
                return
            
            # Get task details for table
            headers = ["ID", "Title", "Status", "Iterations"]
            rows = []
            
            for task_id in task_ids:
                try:
                    task = self.manager.get_task(args.project, task_id)
                    rows.append([
                        task.id,
                        task.title[:40] + "..." if len(task.title) > 40 else task.title,
                        task.status.value,
                        str(task.total_iterations)
                    ])
                except TaskNotFoundError:
                    continue
            
            print(f"\nTasks in project '{args.project}':")
            print(format_table(headers, rows))
            
        except TaskManagerError as e:
            self.error(str(e))
    
    def show_task(self, args) -> None:
        """Show detailed task information."""
        try:
            details = self.manager.get_task_details(args.project, args.task_id)
            task_data = details["task"]
            
            print(f"\nTask {task_data['id']}: {task_data['title']}")
            print("=" * 50)
            print(f"Status: {task_data['status']}")
            print(f"Project: {task_data['project']}")
            print(f"Created: {task_data['created']}")
            if task_data['started']:
                print(f"Started: {task_data['started']}")
            if task_data['completed']:
                print(f"Completed: {task_data['completed']}")
            print(f"Iterations: {details['iteration_count']}")
            
            if task_data['description']:
                print(f"\nDescription:\n{task_data['description']}")
            
            if task_data['notes']:
                print(f"\nNotes:\n{task_data['notes']}")
            
            # Show current iteration if exists
            current_iter = details.get("current_iteration")
            if current_iter:
                print(f"\nCurrent Iteration ({current_iter.iteration}):")
                print(f"  Status: {current_iter.status.value}")
                print(f"  Started: {current_iter.started}")
                if current_iter.notes:
                    print(f"  Notes: {current_iter.notes}")
                if current_iter.summary:
                    print(f"  Summary: {current_iter.summary}")
                if current_iter.user_feedback:
                    print(f"  Feedback: {current_iter.user_feedback}")
                if current_iter.next_steps:
                    print(f"  Next Steps: {current_iter.next_steps}")
            
        except TaskManagerError as e:
            self.error(str(e))
    
    def set_task_status(self, args) -> None:
        """Set task status."""
        try:
            self.manager.set_task_status(args.project, args.task_id, args.status)
            self.success(f"Set task {args.task_id} status to '{args.status}'")
        except TaskManagerError as e:
            self.error(str(e))
    
    def start_task(self, args) -> None:
        """Start working on a task."""
        try:
            iteration = self.manager.start_task(args.project, args.task_id)
            self.success(f"Started task {args.task_id} - created iteration {iteration.iteration}")
        except TaskManagerError as e:
            self.error(str(e))
    
    def complete_task(self, args) -> None:
        """Complete a task."""
        try:
            self.manager.complete_task(args.project, args.task_id)
            self.success(f"Completed task {args.task_id}")
        except TaskManagerError as e:
            self.error(str(e))
    
    # Iteration commands
    
    def add_iteration_note(self, args) -> None:
        """Add note to current iteration."""
        try:
            self.manager.add_iteration_note(args.project, args.task_id, args.note)
            self.success(f"Added note to task {args.task_id}")
        except TaskManagerError as e:
            self.error(str(e))
    
    def set_iteration_summary(self, args) -> None:
        """Set iteration summary."""
        try:
            self.manager.set_iteration_summary(args.project, args.task_id, args.summary)
            self.success(f"Set summary for task {args.task_id}")
        except TaskManagerError as e:
            self.error(str(e))
    
    def add_user_feedback(self, args) -> None:
        """Add user feedback to iteration."""
        try:
            self.manager.add_user_feedback(args.project, args.task_id, args.feedback)
            self.success(f"Added feedback to task {args.task_id}")
        except TaskManagerError as e:
            self.error(str(e))
    
    def set_next_steps(self, args) -> None:
        """Set next steps for iteration."""
        try:
            self.manager.set_next_steps(args.project, args.task_id, args.next_steps)
            self.success(f"Set next steps for task {args.task_id}")
        except TaskManagerError as e:
            self.error(str(e))
    
    def complete_iteration(self, args) -> None:
        """Complete current iteration."""
        try:
            self.manager.complete_iteration(args.project, args.task_id)
            self.success(f"Completed current iteration for task {args.task_id}")
        except TaskManagerError as e:
            self.error(str(e))
    
    def show_iteration(self, args) -> None:
        """Show iteration details."""
        try:
            iteration = self.manager.get_iteration(args.project, args.task_id, args.iteration)
            
            print(f"\nIteration {iteration.iteration} for task {iteration.task_id}")
            print("=" * 50)
            print(f"Status: {iteration.status.value}")
            print(f"Started: {iteration.started}")
            if iteration.completed:
                print(f"Completed: {iteration.completed}")
            
            if iteration.notes:
                print(f"\nNotes:\n{iteration.notes}")
            if iteration.summary:
                print(f"\nSummary:\n{iteration.summary}")
            if iteration.user_feedback:
                print(f"\nUser Feedback:\n{iteration.user_feedback}")
            if iteration.next_steps:
                print(f"\nNext Steps:\n{iteration.next_steps}")
            
        except TaskManagerError as e:
            self.error(str(e))
    
    def list_iterations(self, args) -> None:
        """List iterations for a task."""
        try:
            iterations = self.manager.list_iterations(args.project, args.task_id)
            if not iterations:
                self.info(f"No iterations found for task {args.task_id}.")
                return
            
            print(f"\nIterations for task {args.task_id}:")
            for iter_num in iterations:
                try:
                    iteration = self.manager.get_iteration(args.project, args.task_id, iter_num)
                    status_symbol = "✓" if iteration.status.value == "completed" else "•"
                    print(f"  {status_symbol} Iteration {iter_num} ({iteration.status.value})")
                except IterationNotFoundError:
                    continue
                    
        except TaskManagerError as e:
            self.error(str(e))
    
    # Status commands
    
    def status(self, args) -> None:
        """Show project status."""
        try:
            status_info = self.manager.get_project_status(args.project)
            if not status_info.get("exists"):
                self.error(f"Project '{args.project}' not found")
            
            print(f"\nProject Status: {args.project}")
            print("=" * 30)
            print(f"Total Tasks: {status_info['total_tasks']}")
            print(f"Completed: {status_info['completed_tasks']}")
            print(f"Pending: {status_info['pending_tasks']}")
            print(f"Progress: {status_info['completion_percentage']:.1f}%")
            
            # Simple progress bar
            completion = status_info['completion_percentage'] / 100
            bar_width = 20
            filled = int(completion * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"[{bar}] {completion:.1%}")
            
        except TaskManagerError as e:
            self.error(str(e))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Simple Task Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Project commands
    proj_create = subparsers.add_parser("create-project", help="Create a new project")
    proj_create.add_argument("name", help="Project name")
    proj_create.add_argument("-d", "--description", help="Project description")
    
    subparsers.add_parser("list-projects", help="List all projects")
    
    proj_status = subparsers.add_parser("set-project-status", help="Set project status")
    proj_status.add_argument("name", help="Project name")
    proj_status.add_argument("status", choices=["active", "completed", "archived"], help="New status")
    
    # Task commands
    task_create = subparsers.add_parser("create-task", help="Create a new task")
    task_create.add_argument("project", help="Project name")
    task_create.add_argument("title", help="Task title")
    task_create.add_argument("-d", "--description", help="Task description")
    task_create.add_argument("-n", "--notes", help="Task notes")
    
    task_list = subparsers.add_parser("list-tasks", help="List tasks in project")
    task_list.add_argument("project", help="Project name")
    
    task_show = subparsers.add_parser("show-task", help="Show task details")
    task_show.add_argument("project", help="Project name")
    task_show.add_argument("task_id", help="Task ID")
    
    task_status = subparsers.add_parser("set-task-status", help="Set task status")
    task_status.add_argument("project", help="Project name")
    task_status.add_argument("task_id", help="Task ID")
    task_status.add_argument("status", choices=["TODO", "IN_PROGRESS", "DONE", "ARCHIVED"], help="New status")
    
    task_start = subparsers.add_parser("start-task", help="Start working on task")
    task_start.add_argument("project", help="Project name")
    task_start.add_argument("task_id", help="Task ID")
    
    task_complete = subparsers.add_parser("complete-task", help="Complete a task")
    task_complete.add_argument("project", help="Project name")
    task_complete.add_argument("task_id", help="Task ID")
    
    # Iteration commands
    iter_note = subparsers.add_parser("add-iteration-note", help="Add note to current iteration")
    iter_note.add_argument("project", help="Project name")
    iter_note.add_argument("task_id", help="Task ID")
    iter_note.add_argument("note", help="Note to add")
    
    iter_summary = subparsers.add_parser("set-iteration-summary", help="Set iteration summary")
    iter_summary.add_argument("project", help="Project name")
    iter_summary.add_argument("task_id", help="Task ID")
    iter_summary.add_argument("summary", help="Iteration summary")
    
    iter_feedback = subparsers.add_parser("add-user-feedback", help="Add user feedback")
    iter_feedback.add_argument("project", help="Project name")
    iter_feedback.add_argument("task_id", help="Task ID")
    iter_feedback.add_argument("feedback", help="User feedback")
    
    iter_next = subparsers.add_parser("set-next-steps", help="Set next steps")
    iter_next.add_argument("project", help="Project name")
    iter_next.add_argument("task_id", help="Task ID")
    iter_next.add_argument("next_steps", help="Next steps")
    
    iter_complete = subparsers.add_parser("complete-iteration", help="Complete current iteration")
    iter_complete.add_argument("project", help="Project name")
    iter_complete.add_argument("task_id", help="Task ID")
    
    iter_show = subparsers.add_parser("show-iteration", help="Show iteration details")
    iter_show.add_argument("project", help="Project name")
    iter_show.add_argument("task_id", help="Task ID")
    iter_show.add_argument("iteration", type=int, help="Iteration number")
    
    iter_list = subparsers.add_parser("list-iterations", help="List task iterations")
    iter_list.add_argument("project", help="Project name")
    iter_list.add_argument("task_id", help="Task ID")
    
    # Status command
    status_cmd = subparsers.add_parser("status", help="Show project status")
    status_cmd.add_argument("project", help="Project name")
    
    # Parse arguments and execute
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = TaskCLI()
    
    # Map commands to methods
    command_map = {
        "create-project": cli.create_project,
        "list-projects": cli.list_projects,
        "set-project-status": cli.set_project_status,
        "create-task": cli.create_task,
        "list-tasks": cli.list_tasks,
        "show-task": cli.show_task,
        "set-task-status": cli.set_task_status,
        "start-task": cli.start_task,
        "complete-task": cli.complete_task,
        "add-iteration-note": cli.add_iteration_note,
        "set-iteration-summary": cli.set_iteration_summary,
        "add-user-feedback": cli.add_user_feedback,
        "set-next-steps": cli.set_next_steps,
        "complete-iteration": cli.complete_iteration,
        "show-iteration": cli.show_iteration,
        "list-iterations": cli.list_iterations,
        "status": cli.status,
    }
    
    if args.command in command_map:
        command_map[args.command](args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()