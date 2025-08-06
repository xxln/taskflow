#!/usr/bin/env python3
"""
Enhanced CLI with shortcuts and improved usability.
"""

import argparse
import sys
from typing import Optional
from .manager import TaskManager, TaskManagerError
from .models import TaskStatus
from .search_utils import TaskSearchEngine
from .templates import TaskTemplates
from .storage import TaskStorage

class EnhancedTaskCLI:
    """Enhanced CLI with shortcuts and batch operations."""
    
    def __init__(self):
        self.manager = TaskManager()
        self.storage = TaskStorage()
        self.search_engine = TaskSearchEngine(self.storage)
        self.templates = TaskTemplates()
        self.shortcuts = {
            'ls': 'list-tasks',
            'new': 'create-task',
            'done': 'complete-task',
            'note': 'add-iteration-note',
            'sum': 'set-iteration-summary',
            'next': 'set-next-steps'
        }
    
    def quick_update(self, args):
        """Quick update for task with note, summary, and next steps in one command."""
        try:
            if args.note:
                self.manager.add_iteration_note(args.project, args.task_id, args.note)
            if args.summary:
                self.manager.set_iteration_summary(args.project, args.task_id, args.summary)
            if args.next_steps:
                self.manager.set_next_steps(args.project, args.task_id, args.next_steps)
            print(f"✓ Updated task {args.task_id}")
        except TaskManagerError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    
    def continue_task(self, args):
        """Continue a completed task with a new iteration."""
        try:
            # Reopen task if needed
            task = self.manager.get_task(args.project, args.task_id)
            if task.status == TaskStatus.DONE:
                self.manager.set_task_status(args.project, args.task_id, "IN_PROGRESS")
            
            # Start new iteration
            iteration = self.manager.start_task(args.project, args.task_id)
            
            # Add reason if provided
            if args.reason:
                self.manager.add_iteration_note(args.project, args.task_id, 
                                               f"Continuation reason: {args.reason}")
            
            print(f"✓ Continuing task {args.task_id} with iteration {iteration.iteration}")
        except TaskManagerError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    
    def clone_task(self, args):
        """Clone an existing task as a template for a new one."""
        try:
            # Get source task
            source_task = self.manager.get_task(args.project, args.source_id)
            
            # Create new task with same structure
            new_task = self.manager.create_task(
                args.project,
                args.title or f"{source_task.title} (copy)",
                source_task.description,
                args.notes or source_task.notes
            )
            
            print(f"✓ Created task {new_task.id} from template {args.source_id}")
        except TaskManagerError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    
    def search_tasks(self, args):
        """Search across all projects for tasks matching query."""
        try:
            results = self.search_engine.search_across_projects(
                args.query, 
                status_filter=args.status if hasattr(args, 'status') else None
            )
            
            if not results:
                print(f"No tasks found matching '{args.query}'")
                return
            
            print(f"\nFound {len(results)} task(s) matching '{args.query}':")
            print("-" * 60)
            
            for result in results:
                print(f"[{result['project']}] {result['task_id']}: {result['title']}")
                print(f"  Status: {result['status']}")
                if result['match_context']:
                    print(f"  Match: {result['match_context']}")
                print()
                
        except Exception as e:
            print(f"ERROR: Search failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    def create_from_template(self, args):
        """Create a new task from a template."""
        try:
            # Get template
            template = self.templates.get_template(args.template)
            
            # Prepare variables
            variables = {}
            if hasattr(args, 'variables') and args.variables:
                for var_pair in args.variables:
                    if '=' in var_pair:
                        key, value = var_pair.split('=', 1)
                        variables[key] = value
            
            # Apply template
            task_data = self.templates.apply_template(args.template, variables)
            
            # Create task
            new_task = self.manager.create_task(
                args.project,
                task_data.get('title', 'New Task'),
                task_data.get('description', ''),
                task_data.get('notes', '')
            )
            
            print(f"✓ Created task {new_task.id} from template '{args.template}'")
            
        except TaskManagerError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    
    def list_templates(self, args):
        """List available task templates."""
        templates = self.templates.list_templates()
        
        print("\nAvailable Templates:")
        print("-" * 30)
        for template_name in templates:
            template = self.templates.get_template(template_name)
            print(f"• {template_name}")
            if 'title' in template:
                print(f"  Title pattern: {template['title']}")
        print()

def setup_enhanced_parser():
    """Setup enhanced argument parser with shortcuts."""
    parser = argparse.ArgumentParser(
        description="Enhanced Task Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Quick update command
    quick = subparsers.add_parser("quick", help="Quick update task with multiple fields")
    quick.add_argument("project", help="Project name")
    quick.add_argument("task_id", help="Task ID")
    quick.add_argument("-n", "--note", help="Add note")
    quick.add_argument("-s", "--summary", help="Set summary")
    quick.add_argument("-x", "--next-steps", help="Set next steps")
    
    # Continue task command
    cont = subparsers.add_parser("continue", help="Continue a completed task")
    cont.add_argument("project", help="Project name")
    cont.add_argument("task_id", help="Task ID")
    cont.add_argument("-r", "--reason", help="Reason for continuation")
    
    # Clone task command
    clone = subparsers.add_parser("clone", help="Clone task as template")
    clone.add_argument("project", help="Project name")
    clone.add_argument("source_id", help="Source task ID")
    clone.add_argument("-t", "--title", help="New task title")
    clone.add_argument("-n", "--notes", help="Override notes")
    
    # Search command
    search = subparsers.add_parser("search", help="Search tasks across projects")
    search.add_argument("query", help="Search query")
    search.add_argument("-s", "--status", help="Filter by status")
    
    # Template commands
    template_new = subparsers.add_parser("new-from-template", help="Create task from template")
    template_new.add_argument("project", help="Project name")
    template_new.add_argument("template", help="Template name")
    template_new.add_argument("-v", "--variables", nargs="*", help="Template variables (key=value)")
    
    templates_list = subparsers.add_parser("templates", help="List available templates")
    
    return parser
