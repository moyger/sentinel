# Sentinel Skills Directory

This directory contains custom skills that extend Sentinel's capabilities.

## What are Skills?

Skills are modular capabilities that Sentinel can use to perform specific tasks. Each skill is a self-contained directory with:

- **SKILL.md** - Instructions and metadata for the skill
- **Supporting files** - Python scripts, data files, or other resources

## Skill Structure

```
.claude/skills/
├── email-responder/
│   ├── SKILL.md          # Skill instructions and metadata
│   └── templates/        # Email templates
├── meeting-summarizer/
│   ├── SKILL.md
│   └── summarizer.py
└── web-search/
    ├── SKILL.md
    └── search.py
```

## Creating a New Skill

1. Create a new directory in `.claude/skills/`
2. Add a `SKILL.md` file with skill metadata
3. Add any supporting scripts or files
4. Test the skill using the skill testing framework

See [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md) for the standard format.

## Security

- All skills run locally only
- No external skill registries
- Skills are sandboxed with resource limits
- Input sanitization and output validation

## Available Skills

Skills will be discovered automatically. Run `python -m src.skills.skill_manager list` to see all available skills.
