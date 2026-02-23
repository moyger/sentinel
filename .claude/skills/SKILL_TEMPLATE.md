# Skill Template

Use this template to create new skills for Sentinel.

## Metadata

```yaml
name: skill-name
version: 1.0.0
author: Your Name
description: Brief description of what this skill does
category: utility|communication|research|automation|analysis
tags: [tag1, tag2, tag3]
```

## Requirements

List any dependencies or requirements:
- Python packages (add to requirements.txt)
- API keys or credentials
- External tools or services

## Usage

Describe how to use the skill:

```
Example invocation or command
```

## Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| param1 | string | Yes | Description | - |
| param2 | number | No | Description | 10 |

## Examples

### Example 1: Basic Usage

**Input:**
```
Example input
```

**Output:**
```
Expected output
```

### Example 2: Advanced Usage

**Input:**
```
Another example
```

**Output:**
```
Expected output
```

## Implementation

Describe the implementation approach:

1. Step 1
2. Step 2
3. Step 3

## Files

- `SKILL.md` - This file
- `script.py` - Main skill script
- `data/` - Supporting data files

## Testing

How to test this skill:

```bash
python -m src.skills.skill_manager test skill-name
```

## Security Considerations

- Input validation: How inputs are validated
- Output sanitization: How outputs are cleaned
- Resource limits: Memory, time, network restrictions
- Permissions: What this skill can/cannot access

## Notes

Any additional notes, limitations, or future improvements.

## Version History

- **1.0.0** (2026-02-23) - Initial version
