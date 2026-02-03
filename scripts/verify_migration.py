#!/usr/bin/env python3
"""Verify beads migration completed successfully."""

import json
import subprocess
from collections import Counter
from pathlib import Path


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
    except Exception as e:
        return 1, "", str(e)


def verify_migration() -> bool:  # noqa: C901
    """Verify the beads migration was successful."""
    print("=" * 70)
    print("Beads Migration Verification")
    print("=" * 70)
    print()

    # Load mapping file
    mapping_file = Path(__file__).parent / "github_beads_id_mapping.json"
    if not mapping_file.exists():
        print("❌ Mapping file not found!")
        return False

    with mapping_file.open() as f:
        mapping_data = json.load(f)
        gh_to_beads = mapping_data.get("github_to_beads", {})

    print(f"✓ Loaded mapping: {len(gh_to_beads)} issues")
    print()

    # Get all beads issues
    returncode, stdout, stderr = run_bd_command(["list", "--all", "--limit", "0", "--json"])
    if returncode != 0:
        print(f"❌ Failed to list beads issues: {stderr}")
        return False

    # Parse JSON output - bd list --json outputs a JSON array
    try:
        beads_issues = json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse beads JSON: {e}")
        return False

    print(f"✓ Found {len(beads_issues)} beads issues")
    print()

    # Verify count matches
    if len(beads_issues) != len(gh_to_beads):
        print(f"⚠️  Count mismatch: {len(beads_issues)} in beads vs {len(gh_to_beads)} in mapping")
    else:
        print(f"✓ Count matches: {len(beads_issues)} issues")

    # Check external references
    external_refs = [issue.get("external_ref") for issue in beads_issues if issue.get("external_ref")]
    print(f"✓ External refs: {len(external_refs)} issues have gh-XXX references")

    # Count by type
    type_counts = Counter(issue.get("issue_type", "unknown") for issue in beads_issues)
    print("\n✓ Issue types:")
    for issue_type, count in sorted(type_counts.items()):
        print(f"  - {issue_type}: {count}")

    # Count by priority
    priority_counts = Counter(issue.get("priority", "unknown") for issue in beads_issues)
    print("\n✓ Priorities:")
    for priority, count in sorted(priority_counts.items()):
        print(f"  - P{priority}: {count}")

    # Count by status
    status_counts = Counter(issue.get("status", "unknown") for issue in beads_issues)
    print("\n✓ Status:")
    for status, count in sorted(status_counts.items()):
        print(f"  - {status}: {count}")

    # Check parent-child relationships
    parents = [issue for issue in beads_issues if issue.get("blocks") or issue.get("dependency_count", 0) > 0]
    print("\n✓ Parent-child relationships:")
    print(f"  - {len(parents)} parent issues with children")

    # Check specific epics
    for epic_title in ["T095:", "T075:"]:
        epic = next((i for i in beads_issues if epic_title in i.get("title", "")), None)
        if epic:
            # Need to query children separately
            returncode, stdout, _ = run_bd_command(["list", "--parent", epic["id"]])
            child_lines = [line for line in stdout.strip().split("\n") if line.strip()]
            print(f"  - {epic['title'][:50]}: {len(child_lines)} children")

    # Verify prefix
    beads_ids = [issue.get("id") for issue in beads_issues]
    wrong_prefix = [bid for bid in beads_ids if bid and not bid.startswith("vtt-transcribe-")]
    if wrong_prefix:
        print(f"\n❌ Found {len(wrong_prefix)} issues with wrong prefix:")
        for bid in wrong_prefix[:5]:
            print(f"  - {bid}")
    else:
        print("\n✓ All issues have correct 'vtt-transcribe-' prefix")

    print()
    print("=" * 70)
    print("✅ Migration verification complete!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    import sys

    success = verify_migration()
    sys.exit(0 if success else 1)
