#!/usr/bin/env python3
"""
Task Creator skill for Sentinel.

Creates Asana tasks from natural language input.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

from date_parser import extract_task_parts

# Import Asana SDK
try:
    import asana
except ImportError:
    print(json.dumps({
        'success': False,
        'error': 'Asana package not installed. Run: pip install asana'
    }))
    sys.exit(1)


def create_task(parameters: dict) -> dict:
    """
    Create an Asana task from parameters.

    Args:
        parameters: Dict with 'text', optional 'project_gid', 'assignee', 'priority'

    Returns:
        Result dictionary
    """
    # Validate required parameters
    if 'text' not in parameters:
        return {
            'success': False,
            'error': 'Required parameter "text" is missing'
        }

    text = parameters['text']
    project_gid = parameters.get('project_gid')
    assignee = parameters.get('assignee', 'me')
    priority = parameters.get('priority', 'medium')

    # Get Asana credentials from environment
    asana_token = os.environ.get('ASANA_TOKEN')
    workspace_gid = os.environ.get('ASANA_WORKSPACE_GID')

    if not asana_token:
        return {
            'success': False,
            'error': 'ASANA_TOKEN not found in environment variables'
        }

    if not workspace_gid and not project_gid:
        return {
            'success': False,
            'error': 'Either ASANA_WORKSPACE_GID or project_gid parameter is required'
        }

    # Parse task components
    task_parts = extract_task_parts(text)
    task_name = task_parts['title']
    task_description = task_parts['description']
    due_date = task_parts['due_date']

    # Initialize Asana client
    try:
        client = asana.Client.access_token(asana_token)
        # Disable client-side rate limiting (we handle it)
        client.headers = {'asana-enable': 'new_user_task_lists'}

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to initialize Asana client: {str(e)}'
        }

    # Build task data
    task_data = {
        'name': task_name,
        'workspace': workspace_gid if workspace_gid else None,
    }

    # Add description if present
    if task_description:
        task_data['notes'] = task_description

    # Add project if specified
    if project_gid:
        task_data['projects'] = [project_gid]

    # Add due date if parsed
    if due_date:
        task_data['due_on'] = due_date

    # Create the task
    try:
        result = client.tasks.create(task_data)
        task_gid = result['gid']

        # Add priority tag if not medium
        if priority in ['high', 'low']:
            try:
                # Get workspace tags
                tags = list(client.tags.find_by_workspace(workspace_gid, opt_fields=['name', 'gid']))

                # Find or create priority tag
                priority_tag_name = f"{priority.capitalize()} Priority"
                priority_tag = next((t for t in tags if t['name'] == priority_tag_name), None)

                if priority_tag:
                    client.tasks.add_tag(task_gid, {'tag': priority_tag['gid']})
            except Exception as tag_error:
                # Non-critical error, task is still created
                pass

        # Assign task if specified
        if assignee and assignee != 'me':
            try:
                # Find user by email
                users = list(client.users.find_by_workspace(workspace_gid, opt_fields=['email', 'gid']))
                user = next((u for u in users if u.get('email') == assignee), None)

                if user:
                    client.tasks.update(task_gid, {'assignee': user['gid']})
            except Exception as assign_error:
                # Non-critical error
                pass

        # Build task URL
        if project_gid:
            task_url = f"https://app.asana.com/0/{project_gid}/{task_gid}"
        else:
            task_url = f"https://app.asana.com/0/0/{task_gid}"

        # Build success response
        response = {
            'success': True,
            'task_gid': task_gid,
            'task_name': task_name,
            'task_url': task_url,
            'message': 'Task created successfully'
        }

        if due_date:
            response['due_date'] = due_date
            response['message'] = 'Task created successfully with due date'

        if project_gid:
            response['message'] = 'Task created in project successfully'

        return response

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to create task: {str(e)}'
        }


def main():
    """Main entry point."""
    # Get parameters from command line
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'No parameters provided. Usage: task-creator.py \'{"text": "..."}\''
        }))
        sys.exit(1)

    try:
        parameters = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({
            'success': False,
            'error': f'Invalid JSON parameters: {str(e)}'
        }))
        sys.exit(1)

    # Create task
    result = create_task(parameters)

    # Output result as JSON
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
