# Task Creator

Create tasks in Asana from natural language input.

## Metadata

```yaml
name: task-creator
version: 1.0.0
author: Sentinel Team
description: Create tasks in Asana from text descriptions with automatic parsing of title, details, and due dates
category: automation
tags: [asana, tasks, productivity, automation]
```

## Requirements

- Asana Personal Access Token (ASANA_TOKEN in .env)
- Asana Workspace GID (ASANA_WORKSPACE_GID in .env)
- Python packages: asana, python-dateutil

## Usage

This skill creates tasks in Asana from natural language input. It automatically parses:
- Task title (first line or sentence)
- Task description (remaining text)
- Due date (if mentioned using natural language like "tomorrow", "next Monday", etc.)

```python
# Example usage
result = await skill_manager.execute_skill("task-creator", {
    "text": "Review Q1 budget proposal - Need to analyze the budget and provide feedback by Friday",
    "project_gid": "1234567890"  # Optional: specific project
})
```

## Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| text | string | Yes | Natural language task description | - |
| project_gid | string | No | Asana project GID to add task to | None |
| assignee | string | No | Email of person to assign task to | me |
| priority | string | No | Task priority (high, medium, low) | medium |

## Examples

### Example 1: Simple Task

**Input:**
```json
{
  "text": "Call the client about the proposal"
}
```

**Output:**
```json
{
  "success": true,
  "task_gid": "1234567890",
  "task_name": "Call the client about the proposal",
  "task_url": "https://app.asana.com/0/0/1234567890",
  "message": "Task created successfully"
}
```

### Example 2: Task with Due Date

**Input:**
```json
{
  "text": "Finish the presentation slides by next Friday",
  "priority": "high"
}
```

**Output:**
```json
{
  "success": true,
  "task_gid": "1234567891",
  "task_name": "Finish the presentation slides",
  "due_date": "2026-03-07",
  "task_url": "https://app.asana.com/0/0/1234567891",
  "message": "Task created successfully with due date"
}
```

### Example 3: Detailed Task with Project

**Input:**
```json
{
  "text": "Update documentation\n\nNeed to add examples for the new API endpoints and update the changelog. This should be done before the release.",
  "project_gid": "1234567890",
  "priority": "high"
}
```

**Output:**
```json
{
  "success": true,
  "task_gid": "1234567892",
  "task_name": "Update documentation",
  "task_url": "https://app.asana.com/0/1234567890/1234567892",
  "message": "Task created in project successfully"
}
```

## Implementation

1. Parse input text to extract:
   - Task title (first sentence or line)
   - Task description (remaining text)
   - Due date hints (tomorrow, next week, Friday, etc.)

2. Connect to Asana API using token from environment

3. Create task with parsed information:
   - Set task name and description
   - Parse and set due date if mentioned
   - Add to project if specified
   - Set priority tags
   - Assign to user

4. Return task details including URL

## Files

- `SKILL.md` - This file
- `task-creator.py` - Main skill script
- `date_parser.py` - Natural language date parsing

## Testing

Test the skill using the skill manager:

```bash
python -m src.skills.skill_manager test task-creator --text "Write blog post about AI agents"
```

Or test directly:

```bash
cd /Users/karlomarceloestrada/sentinel
source venv/bin/activate
python .claude/skills/task-creator/task-creator.py '{"text": "Test task"}'
```

## Security Considerations

- **Input validation**: Text input is sanitized before sending to Asana API
- **Output sanitization**: API responses are validated before returning
- **Resource limits**: API calls are limited to prevent abuse
- **Permissions**: Uses read-write Asana token (scoped to user's workspace)
- **Rate limiting**: Respects Asana API rate limits (150 req/min)

## Notes

- Requires valid Asana credentials in .env file
- Due date parsing supports common natural language patterns
- If no project is specified, task is created in default workspace
- Priority is set using Asana tags (High Priority, Medium Priority, Low Priority)
- Task URL is constructed from task GID and project GID

## Version History

- **1.0.0** (2026-02-23) - Initial version with basic task creation and date parsing
