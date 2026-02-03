---
name: beads
description: Beads CLI (bd) reference for lightweight issue tracking with first-class dependency support.
tools: ["terminal"]
---

# Beads CLI (bd)

Use `bd` for all task and issue tracking. Issues are chained together like beads with dependency support.

## Core Workflow Commands

### Quick Commands
```bash
bd ready                             # Find available work (no blockers)
bd show <id>                         # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>                        # Complete work
bd sync                              # Sync with git (export to JSONL)
```

### View Tasks
```bash
bd list                              # List open issues (default limit: 50)
bd list --all                        # Include closed issues
bd list --status in_progress         # Filter by status
bd list --priority P0                # Filter by priority (P0-P4)
bd list --assignee @me               # Your assigned issues
bd list --ready                      # Ready to work (no blockers)
bd list --pretty                     # Tree format with status symbols
bd list --type epic                  # Filter by type
bd list --label bug                  # Filter by label
```

### View Issue Details
```bash
bd show T095_002                     # Show issue details
bd show T095_002 --children          # Show with children
bd show T095_002 --refs              # Show reverse references
```

### Create Issues
```bash
bd create "Fix dependency check"                # Simple task
bd create "Add feature" --type feature          # Specify type
bd create "P0 bug" --priority P0 --type bug     # With priority
bd create "Epic name" --type epic               # Create epic
bd create "Subtask" --parent T095               # Create child issue
```

### Update Issues
```bash
bd update T095_002 --status in_progress   # Start working
bd update T095_002 --status closed        # Complete task
bd update --claim                         # Claim last touched issue
bd update T095_002 --assignee @me         # Assign to yourself
bd update T095_002 --priority P1          # Change priority
bd update T095_002 --add-label bug        # Add label
bd update T095_002 --title "New title"    # Update title
```

### Quick Status Changes
```bash
# Common workflow aliases
bd update <id> --status open              # Open/reopen
bd update <id> --status in_progress       # Start work
bd update <id> --status blocked           # Blocked
bd update <id> --status closed            # Complete
```

### Dependencies & Structure
```bash
bd dep add T095_002 --blocks T095_003     # Add dependency
bd dep list T095_002                      # List dependencies
bd children T095                          # List child issues
bd graph                                  # Show dependency graph
bd epic list                              # List epics
```

### Search & Filter
```bash
bd search "dependency check"              # Text search
bd list --title-contains "test"           # Filter by title
bd list --created-after 2025-01-01        # Date filters
bd list --updated-after "1 week ago"      # Relative dates
```

## Advanced Features

### JSON Output
```bash
bd list --json                            # JSON output
bd show T095_002 --json                   # JSON issue details
```

### Status & Statistics
```bash
bd status                                 # Database overview
bd count --status open                    # Count by filter
bd stale                                  # Show stale issues
```

### Export & Sync
```bash
bd export --format jsonl                  # Export to JSONL
bd sync                                   # Sync to JSONL (git)
```

### Maintenance
```bash
bd init                                   # Initialize in repo
bd doctor                                 # Check installation health
bd info                                   # Show database info
```

## Common Filters

- `--status`: open, in_progress, blocked, deferred, closed
- `--type`: bug, feature, task, epic, chore
- `--priority`: P0 (highest) through P4 (lowest)
- `--assignee`: @me or username
- `--label`: Filter by labels (AND logic)

## Task Workflow Example

```bash
# 1. View available tasks
bd ready                             # Find work with no blockers
bd list --ready --pretty             # Alternative with tree view

# 2. Start work on a task
bd update T095_002 --claim           # Atomic claim

# 3. View task details
bd show T095_002

# 4. Mark complete
bd close T095_002                    # Quick close
bd update T095_002 --status closed   # Alternative
```

## Session Completion (Landing the Plane)

When ending a work session, complete ALL steps:

1. **File issues for remaining work** - Create follow-up tasks
2. **Run quality gates** - `make lint && make test`
3. **Update issue status** - Close finished, update in-progress
4. **PUSH TO REMOTE** (MANDATORY):
   ```bash
   git pull --rebase
   bd sync                           # Sync beads to JSONL
   git push
   git status                        # Verify "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL**: Work is NOT complete until `git push` succeeds. Never stop before pushing.

## Setup

```bash
bd init                              # Initialize in repository
bd onboard                           # Get started guide
```

## References
- GitHub: https://github.com/steveyegge/beads
- Install: `curl -sSL https://beads.link/install.sh | bash`
