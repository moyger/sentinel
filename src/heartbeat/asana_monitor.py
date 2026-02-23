"""
Asana monitor for checking tasks and project updates.

Uses Asana API to fetch tasks assigned to the user and detect overdue items.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asana

from .base_monitor import BaseMonitor, Alert
from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)


class AsanaMonitor(BaseMonitor):
    """
    Monitor for Asana tasks and projects.

    Checks for:
    - Tasks assigned to user
    - Overdue tasks
    - Tasks due today
    - Tasks due this week
    - High-priority tasks
    """

    def __init__(self):
        """Initialize Asana monitor."""
        super().__init__("asana")
        self.client = None
        self.user_gid = None

    async def initialize(self) -> None:
        """Initialize Asana API connection."""
        logger.info("Initializing Asana monitor...")

        try:
            # Create Asana client
            self.client = asana.Client.access_token(config.ASANA_ACCESS_TOKEN)

            # Get user info
            user = self.client.users.get_user('me')
            self.user_gid = user['gid']

            logger.info(
                "Asana monitor initialized",
                user_name=user.get('name'),
                user_gid=self.user_gid
            )

        except Exception as e:
            logger.error("Failed to initialize Asana monitor", error=str(e), exc_info=True)
            raise

    async def cleanup(self) -> None:
        """Clean up Asana resources."""
        logger.info("Cleaning up Asana monitor...")
        self.client = None
        self.user_gid = None

    async def check(self) -> Dict[str, Any]:
        """
        Check Asana for tasks needing attention.

        Returns:
            Dictionary with alerts and task data
        """
        if not self.client:
            raise RuntimeError("Asana monitor not initialized")

        alerts = []
        tasks_data = []

        try:
            # Fetch tasks assigned to user
            logger.debug("Fetching Asana tasks...")

            # Get tasks from user's workspaces
            workspaces = list(self.client.workspaces.get_workspaces())

            for workspace in workspaces:
                workspace_gid = workspace['gid']

                # Fetch incomplete tasks assigned to user
                tasks = self.client.tasks.get_tasks(
                    {
                        'assignee': self.user_gid,
                        'workspace': workspace_gid,
                        'completed_since': 'now',  # Only incomplete
                        'opt_fields': 'name,due_on,due_at,completed,projects,tags,notes'
                    }
                )

                for task in tasks:
                    task_data = self._parse_task(task)
                    tasks_data.append(task_data)

                    # Check if task needs alerts
                    task_alerts = self._check_task_priority(task_data)
                    alerts.extend([alert.to_dict() for alert in task_alerts])

            # Sort tasks by due date
            tasks_data.sort(key=lambda t: t['due_date'] or datetime.max)

            logger.info(
                "Asana check completed",
                tasks_count=len(tasks_data),
                alerts_count=len(alerts)
            )

            return {
                "alerts": alerts,
                "data": {
                    "tasks_count": len(tasks_data),
                    "tasks": tasks_data[:20]  # Return top 20
                },
                "metadata": {
                    "user_gid": self.user_gid,
                    "workspaces_checked": len(workspaces)
                }
            }

        except Exception as e:
            logger.error("Asana check failed", error=str(e), exc_info=True)
            raise

    def _parse_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Asana task into structured data.

        Args:
            task: Asana API task object

        Returns:
            Parsed task data
        """
        # Parse due date
        due_date = None
        if task.get('due_on'):
            due_date = datetime.strptime(task['due_on'], '%Y-%m-%d')
        elif task.get('due_at'):
            due_date = datetime.fromisoformat(task['due_at'].replace('Z', '+00:00'))

        # Get project names
        projects = task.get('projects', [])
        project_names = [p.get('name', '') for p in projects]

        # Get tags
        tags = task.get('tags', [])
        tag_names = [t.get('name', '') for t in tags]

        return {
            "gid": task.get('gid'),
            "name": task.get('name', 'Untitled Task'),
            "due_date": due_date,
            "completed": task.get('completed', False),
            "projects": project_names,
            "tags": tag_names,
            "notes": task.get('notes', '')
        }

    def _check_task_priority(self, task: Dict[str, Any]) -> List[Alert]:
        """
        Check if task needs alerts.

        Args:
            task: Parsed task data

        Returns:
            List of alerts for this task
        """
        alerts = []

        if not task['due_date']:
            return alerts  # Skip tasks without due dates

        now = datetime.now(task['due_date'].tzinfo) if task['due_date'].tzinfo else datetime.now()
        days_until_due = (task['due_date'].date() - now.date()).days

        # Overdue tasks
        if days_until_due < 0:
            alerts.append(self.create_alert(
                title=f"Overdue Task: {task['name']}",
                message=self._format_task_message(task, days_until_due),
                priority="urgent",
                metadata={
                    "task_gid": task['gid'],
                    "days_overdue": abs(days_until_due),
                    "status": "overdue"
                }
            ))

        # Due today
        elif days_until_due == 0:
            alerts.append(self.create_alert(
                title=f"Due Today: {task['name']}",
                message=self._format_task_message(task, days_until_due),
                priority="urgent",
                metadata={
                    "task_gid": task['gid'],
                    "status": "due_today"
                }
            ))

        # Due tomorrow
        elif days_until_due == 1:
            alerts.append(self.create_alert(
                title=f"Due Tomorrow: {task['name']}",
                message=self._format_task_message(task, days_until_due),
                priority="normal",
                metadata={
                    "task_gid": task['gid'],
                    "status": "due_tomorrow"
                }
            ))

        # Due this week (2-7 days)
        elif 2 <= days_until_due <= 7:
            alerts.append(self.create_alert(
                title=f"Due This Week: {task['name']}",
                message=self._format_task_message(task, days_until_due),
                priority="low",
                metadata={
                    "task_gid": task['gid'],
                    "days_until_due": days_until_due,
                    "status": "due_this_week"
                }
            ))

        return alerts

    def _format_task_message(self, task: Dict[str, Any], days_until_due: int) -> str:
        """
        Format task details into alert message.

        Args:
            task: Parsed task data
            days_until_due: Days until due date (negative if overdue)

        Returns:
            Formatted message
        """
        lines = []

        # Due date info
        if days_until_due < 0:
            lines.append(f"Overdue by {abs(days_until_due)} day{'s' if abs(days_until_due) > 1 else ''}")
        elif days_until_due == 0:
            lines.append("Due today")
        elif days_until_due == 1:
            lines.append("Due tomorrow")
        else:
            lines.append(f"Due in {days_until_due} days")

        due_str = task['due_date'].strftime("%A, %B %d")
        lines.append(f"Date: {due_str}")

        # Projects
        if task['projects']:
            lines.append(f"Project: {', '.join(task['projects'][:2])}")

        # Tags
        if task['tags']:
            lines.append(f"Tags: {', '.join(task['tags'][:3])}")

        # Notes (first line only)
        if task['notes']:
            notes_line = task['notes'].split('\n')[0][:100]
            lines.append(f"Notes: {notes_line}")

        return '\n'.join(lines)
