"""
Natural language date parser for task due dates.

Supports common patterns like:
- tomorrow, today
- next Monday, this Friday
- in 3 days, in 2 weeks
- March 15, 2026-03-15
"""

import re
from datetime import datetime, timedelta
from typing import Optional


def parse_due_date(text: str) -> Optional[str]:
    """
    Parse natural language date from text.

    Args:
        text: Text containing date reference

    Returns:
        ISO date string (YYYY-MM-DD) or None
    """
    text_lower = text.lower()

    # Today
    if 'today' in text_lower:
        return datetime.now().date().isoformat()

    # Tomorrow
    if 'tomorrow' in text_lower:
        return (datetime.now().date() + timedelta(days=1)).isoformat()

    # Next week
    if 'next week' in text_lower:
        return (datetime.now().date() + timedelta(weeks=1)).isoformat()

    # This week
    if 'this week' in text_lower:
        # End of this week (Friday)
        days_until_friday = (4 - datetime.now().weekday()) % 7
        return (datetime.now().date() + timedelta(days=days_until_friday)).isoformat()

    # Weekdays (next Monday, this Friday, etc.)
    weekdays = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }

    for day_name, day_num in weekdays.items():
        pattern = rf'\b(next|this)\s+{day_name}\b'
        match = re.search(pattern, text_lower)
        if match:
            modifier = match.group(1)
            current_day = datetime.now().weekday()

            if modifier == 'next':
                # Next occurrence of that day
                days_ahead = (day_num - current_day + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week if it's the same day
            else:  # 'this'
                # This week's occurrence
                days_ahead = (day_num - current_day) % 7

            target_date = datetime.now().date() + timedelta(days=days_ahead)
            return target_date.isoformat()

    # "in X days/weeks"
    in_days_match = re.search(r'\bin\s+(\d+)\s+days?\b', text_lower)
    if in_days_match:
        days = int(in_days_match.group(1))
        return (datetime.now().date() + timedelta(days=days)).isoformat()

    in_weeks_match = re.search(r'\bin\s+(\d+)\s+weeks?\b', text_lower)
    if in_weeks_match:
        weeks = int(in_weeks_match.group(1))
        return (datetime.now().date() + timedelta(weeks=weeks)).isoformat()

    # "by [day]" patterns
    by_match = re.search(r'\bby\s+(next|this)\s+(\w+)', text_lower)
    if by_match:
        modifier = by_match.group(1)
        day_candidate = by_match.group(2)

        if day_candidate in weekdays:
            day_num = weekdays[day_candidate]
            current_day = datetime.now().weekday()

            if modifier == 'next':
                days_ahead = (day_num - current_day + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
            else:
                days_ahead = (day_num - current_day) % 7

            target_date = datetime.now().date() + timedelta(days=days_ahead)
            return target_date.isoformat()

    # ISO date format (YYYY-MM-DD)
    iso_match = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', text)
    if iso_match:
        return iso_match.group(0)

    # No date found
    return None


def extract_task_parts(text: str) -> dict:
    """
    Extract task components from text.

    Args:
        text: Task text

    Returns:
        Dictionary with title, description, and due_date
    """
    lines = text.strip().split('\n')

    # First line is the title
    title = lines[0].strip()

    # Clean up title (remove date references for cleaner title)
    # Remove common date patterns from title
    title = re.sub(r'\s+(by|on|before)\s+(next|this)?\s*\w+\s*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+(tomorrow|today)\s*$', '', title, flags=re.IGNORECASE)

    # Remaining lines are description
    description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''

    # Parse due date from entire text
    due_date = parse_due_date(text)

    return {
        'title': title,
        'description': description,
        'due_date': due_date
    }


# Test the parser
if __name__ == '__main__':
    test_cases = [
        "Call client tomorrow",
        "Finish presentation by next Friday",
        "Review code this week",
        "Schedule meeting in 3 days",
        "Submit report by this Monday",
        "Write blog post\n\nNeed to cover AI agents and automation. Should be done by next week.",
    ]

    for text in test_cases:
        result = extract_task_parts(text)
        print(f"\nInput: {text}")
        print(f"Title: {result['title']}")
        print(f"Due: {result['due_date']}")
        if result['description']:
            print(f"Desc: {result['description']}")
