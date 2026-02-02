# Scripts Directory

This directory contains utility scripts for project management and migration tasks.

## Issue Export Script

### Purpose
Export GitHub issues to structured formats (JSON/CSV) for migration to beads or other tracking systems.

### Usage

```bash
python scripts/export_issues.py
```

### Output Files

The script generates two files with timestamps:

1. **JSON Export** (`github_issues_export_YYYYMMDD_HHMMSS.json`)
   - Complete issue data including comments
   - Full metadata (labels, assignees, milestones)
   - Suitable for programmatic processing and beads import

2. **CSV Export** (`github_issues_export_YYYYMMDD_HHMMSS.csv`)
   - Flattened issue data for spreadsheet analysis
   - Includes issue number, title, state, labels, dates
   - Body preview and comment counts

### Requirements

- GitHub CLI (`gh`) must be installed and authenticated
- Requires read access to the repository

### Data Included

For each issue:
- Number, title, state (open/closed)
- Body content
- Labels and milestone
- Author and assignees
- Created, updated, and closed timestamps
- All comments with author and timestamps
- Issue URL

### Notes

- Export files are gitignored by default (contain full issue history)
- The script can be re-run safely to generate fresh exports
- Rate limiting: Script respects GitHub API rate limits
- Large repositories: May take several minutes for repos with many issues
