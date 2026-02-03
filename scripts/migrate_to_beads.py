#!/usr/bin/env python3
"""
T095.3: Create migration script to create beads issues via API.

Reads the mapping from T095.2 and creates beads issues, preserving
parent-child relationships while allowing beads to assign new IDs.
"""

# type: ignore[attr-defined,index,operator,return-value]

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_bd_command(args: list[str]) -> tuple[int, str, str]:
    """Run a bd CLI command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["bd", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "Error: bd command not found. Is beads installed?"


def extract_issue_id(output: str) -> str | None:
    """Extract issue ID from bd create output (e.g., 'Created issue: video_to_text-c8h')."""
    for line in output.split("\n"):
        if "Created issue:" in line or "created issue:" in line.lower():
            parts = line.split()
            if len(parts) >= 3:
                return parts[-1].strip()
    return None


def create_epic(
    title: str,
    priority: str,
    state: str,
    gh_number: int,
) -> str | None:
    """Create an epic in beads and return the new beads ID."""
    args = [
        "create",
        title,
        "--type",
        "epic",
        "--priority",
        priority,
        "--external-ref",
        f"gh-{gh_number}",
    ]

    returncode, stdout, stderr = run_bd_command(args)

    if returncode != 0:
        print(f"  ❌ Failed to create epic: {stderr}")
        return None

    issue_id = extract_issue_id(stdout)
    if issue_id:
        print(f"  ✅ Created epic {issue_id}: {title[:50]}")

        # Close the issue if it was closed in GitHub
        if state == "CLOSED":
            close_returncode, _, close_stderr = run_bd_command(["close", issue_id])
            if close_returncode == 0:
                print(f"     └─ Closed {issue_id}")
            else:
                print(f"     └─ ⚠️  Failed to close: {close_stderr}")
    else:
        print(f"  ⚠️  Epic created but couldn't extract ID from: {stdout[:100]}")

    return issue_id


def create_child_issue(
    title: str,
    issue_type: str,
    priority: str,
    state: str,
    parent_id: str,
    gh_number: int,
) -> str | None:
    """Create a child issue in beads and return the new beads ID."""
    args = [
        "create",
        title,
        "--type",
        issue_type,
        "--priority",
        priority,
        "--parent",
        parent_id,
        "--external-ref",
        f"gh-{gh_number}",
    ]

    returncode, stdout, stderr = run_bd_command(args)

    if returncode != 0:
        print(f"    ❌ Failed to create child: {stderr}")
        return None

    issue_id = extract_issue_id(stdout)
    if issue_id:
        print(f"    ✅ Created {issue_id}: {title[:45]}")

        # Close if it was closed in GitHub
        if state == "CLOSED":
            close_returncode, _, _ = run_bd_command(["close", issue_id])
            if close_returncode == 0:
                print(f"       └─ Closed {issue_id}")
    else:
        print(f"    ⚠️  Child created but couldn't extract ID from: {stdout[:100]}")

    return issue_id


def create_orphan_issue(
    title: str,
    issue_type: str,
    priority: str,
    state: str,
    gh_number: int,
) -> str | None:
    """Create an orphan (standalone) issue in beads."""
    args = [
        "create",
        title,
        "--type",
        issue_type,
        "--priority",
        priority,
        "--external-ref",
        f"gh-{gh_number}",
    ]

    returncode, stdout, stderr = run_bd_command(args)

    if returncode != 0:
        print(f"  ❌ Failed to create issue: {stderr}")
        return None

    issue_id = extract_issue_id(stdout)
    if issue_id:
        print(f"  ✅ Created {issue_id}: {title[:50]}")

        # Close if it was closed in GitHub
        if state == "CLOSED":
            close_returncode, _, _ = run_bd_command(["close", issue_id])
            if close_returncode == 0:
                print(f"     └─ Closed {issue_id}")

    return issue_id


def migrate_issues(  # noqa: C901
    mapping: dict[str, Any], *, dry_run: bool = False
) -> dict[str, str]:
    """
    Migrate GitHub issues to beads.

    Returns a mapping of GH issue numbers to beads IDs.
    """
    gh_to_beads: dict[str, str] = {}

    if dry_run:
        print("\n🔍 DRY RUN MODE - No issues will be created\n")

    print(f"{'=' * 70}")
    print("Beads Migration - Creating Issues")
    print(f"{'=' * 70}\n")

    # Phase 1: Create epics with children
    print(f"Phase 1: Migrating {len(mapping['epics'])} epics with children\n")

    for gh_num, epic in sorted(mapping["epics"].items(), key=lambda x: int(x[0])):
        print(f"Epic #{gh_num}: {epic['title']}")

        if dry_run:
            print(f"  [DRY RUN] Would create epic with {len(epic['children'])} children")
            for child in epic["children"]:
                print(f"    [DRY RUN] Would create child #{child['gh_number']}: {child['title'][:45]}")
            continue

        # Create the epic
        beads_id = create_epic(
            title=epic["title"],
            priority=epic["priority"],
            state=epic["state"],
            gh_number=int(gh_num),
        )

        if not beads_id:
            print("  ⚠️  Skipping children due to failed epic creation")
            continue

        gh_to_beads[gh_num] = beads_id

        # Create children
        for child in epic["children"]:
            child_id = create_child_issue(
                title=child["title"],
                issue_type=child["type"],
                priority=child["priority"],
                state=child["state"],
                parent_id=beads_id,
                gh_number=child["gh_number"],
            )

            if child_id:
                gh_to_beads[str(child["gh_number"])] = child_id

        print()

    # Phase 2: Create orphan issues
    print(f"\nPhase 2: Migrating {len(mapping['orphans'])} orphan issues\n")

    orphan_count = 0
    for orphan in mapping["orphans"]:
        if dry_run:
            print(f"  [DRY RUN] Would create #{orphan['gh_number']}: {orphan['title'][:50]}")
            continue

        issue_id = create_orphan_issue(
            title=orphan["title"],
            issue_type=orphan["type"],
            priority=orphan["priority"],
            state=orphan["state"],
            gh_number=orphan["gh_number"],
        )

        if issue_id:
            gh_to_beads[str(orphan["gh_number"])] = issue_id
            orphan_count += 1

    if not dry_run:
        print(f"\n  Created {orphan_count} orphan issues")

    return gh_to_beads


def save_id_mapping(gh_to_beads: dict[str, str], output_file: Path) -> None:
    """Save GitHub → Beads ID mapping for reference."""
    mapping_data = {
        "migration_date": "2026-02-03",
        "github_to_beads": gh_to_beads,
        "total_migrated": len(gh_to_beads),
    }

    with open(output_file, "w") as f:
        json.dump(mapping_data, f, indent=2)

    print(f"\n💾 ID mapping saved to: {output_file}")


def print_summary(gh_to_beads: dict[str, str]) -> None:
    """Print migration summary."""
    print(f"\n{'=' * 70}")
    print("Migration Summary")
    print(f"{'=' * 70}\n")

    print(f"Total issues migrated: {len(gh_to_beads)}")
    print("\nGitHub → Beads ID Mapping (first 10):")
    for gh_num, beads_id in sorted(gh_to_beads.items(), key=lambda x: int(x[0]))[:10]:
        print(f"  gh-{gh_num} → {beads_id}")

    if len(gh_to_beads) > 10:
        print(f"  ... and {len(gh_to_beads) - 10} more")

    print(f"\n{'=' * 70}\n")


def main() -> int:
    """Main entry point."""
    scripts_dir = Path(__file__).parent
    mapping_file = scripts_dir / "beads_migration_mapping.json"

    if not mapping_file.exists():
        print(f"Error: Mapping file not found: {mapping_file}")
        print("Run T095.2 (map_issues_to_beads.py) first to generate the mapping.")
        return 1

    # Check if bd is available
    returncode, stdout, _stderr = run_bd_command(["version"])
    if returncode != 0:
        print("Error: bd command not available")
        print("Install beads: curl -sSL https://beads.link/install.sh | bash")
        return 1

    print(f"Using beads: {stdout.strip()}")

    # Load mapping
    with open(mapping_file) as f:
        mapping = json.load(f)

    # Check for dry run flag
    dry_run = "--dry-run" in sys.argv

    # Confirm migration
    if not dry_run:
        print(f"\n⚠️  About to migrate {mapping['total_issues']} GitHub issues to beads")
        print("This will create new beads issues with new IDs.")
        print("Parent-child relationships will be preserved.")
        print("\nPress Ctrl+C to cancel, or Enter to continue...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nMigration cancelled.")
            return 0

    # Run migration
    gh_to_beads = migrate_issues(mapping, dry_run=dry_run)

    if not dry_run and gh_to_beads:
        # Save ID mapping
        id_mapping_file = scripts_dir / "github_beads_id_mapping.json"
        save_id_mapping(gh_to_beads, id_mapping_file)

        # Print summary
        print_summary(gh_to_beads)

        print("Next steps:")
        print("  1. Verify issues with: bd list --all --pretty")
        print("  2. Run T095.4 to verify links and labels")
        print("  3. Run T095.5 to add migration notes and close GitHub issues")
    elif dry_run:
        print(f"\n✅ Dry run complete. {mapping['total_issues']} issues would be created.")
        print("\nRun without --dry-run to actually create the issues:")
        print(f"  python3 {Path(__file__).name}")

    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user.")
        exit(1)
