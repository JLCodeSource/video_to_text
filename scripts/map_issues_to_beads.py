#!/usr/bin/env python3
"""
T095.2: Map GitHub issues to beads structure.

Analyzes exported GitHub issues and creates a mapping plan for beads migration.
Preserves parent-child relationships while allowing beads to assign new IDs.
"""

# type: ignore[attr-defined,index,operator,return-value]

import json
import re
from pathlib import Path
from typing import Any


def extract_parent_id(body: str | None) -> str | None:
    """Extract parent ID from issue body (e.g., '## Parent: T095' -> 'T095')."""
    if not body:
        return None
    match = re.search(r"##\s*Parent:\s*([A-Z0-9_]+)", body)
    return match.group(1) if match else None


def determine_issue_type(issue: dict[str, Any]) -> str:
    """Determine beads issue type from GitHub issue."""
    title = issue.get("title", "").lower()
    labels = [label["name"].lower() for label in issue.get("labels", [])]

    # Check labels first
    if "epic" in labels:
        return "epic"
    if "bug" in labels or "bugfix" in labels:
        return "bug"
    if "enhancement" in labels or "feature" in labels:
        return "feature"
    if "documentation" in labels:
        return "task"
    if "chore" in labels:
        return "chore"

    # Check title patterns
    if "epic" in title or (title.startswith("t0") and "." not in title):
        return "epic"
    if "bug" in title or "fix" in title:
        return "bug"
    if "add" in title or "implement" in title or "feature" in title:
        return "feature"
    if "doc" in title or "readme" in title:
        return "task"

    return "task"  # Default


def map_priority(labels: list[dict[str, Any]]) -> str:
    """Map GitHub labels to beads priority (P0-P4)."""
    label_names = [label["name"].lower() for label in labels]

    if any("critical" in name or "urgent" in name or "p0" in name for name in label_names):
        return "P0"
    if any("high" in name or "p1" in name for name in label_names):
        return "P1"
    if any("low" in name or "p3" in name for name in label_names):
        return "P3"
    if any("p4" in name for name in label_names):
        return "P4"

    return "P2"  # Default: medium priority


def analyze_issues(json_file: Path) -> dict[str, Any]:
    """Analyze exported GitHub issues and create mapping plan."""
    with open(json_file) as f:
        data = json.load(f)

    issues = data["issues"]

    # Build mapping structure
    mapping = {
        "total_issues": len(issues),
        "open_issues": sum(1 for i in issues if i["state"] == "OPEN"),
        "closed_issues": sum(1 for i in issues if i["state"] == "CLOSED"),
        "epics": {},
        "orphans": [],
        "type_counts": {},
        "priority_counts": {},
    }

    # First pass: identify all issues and their properties
    issue_map = {}
    for issue in issues:
        gh_number = issue["number"]
        parent_id = extract_parent_id(issue.get("body"))
        issue_type = determine_issue_type(issue)
        priority = map_priority(issue.get("labels", []))

        issue_map[gh_number] = {
            "gh_number": gh_number,
            "title": issue["title"],
            "body": issue.get("body", ""),
            "state": issue["state"],
            "parent_id": parent_id,
            "type": issue_type,
            "priority": priority,
            "labels": [label["name"] for label in issue.get("labels", [])],
            "url": issue["url"],
        }

        # Count types and priorities
        mapping["type_counts"][issue_type] = mapping["type_counts"].get(issue_type, 0) + 1
        mapping["priority_counts"][priority] = mapping["priority_counts"].get(priority, 0) + 1

    # Second pass: build parent-child relationships
    for gh_number, info in issue_map.items():
        parent_id = info["parent_id"]

        if parent_id:
            # Find parent by looking for issue with this ID in title (e.g., "T095" in "T095: [EPIC] ...")
            parent_issue = None
            for pgh_num, pinfo in issue_map.items():
                # Match exact task ID at start of title or with colon
                title = pinfo["title"]
                if title.startswith((parent_id + ":", parent_id + " ")):
                    parent_issue = pgh_num
                    break

            if parent_issue:
                if parent_issue not in mapping["epics"]:
                    parent_info = issue_map[parent_issue]
                    mapping["epics"][parent_issue] = {
                        "title": parent_info["title"],
                        "type": parent_info["type"],
                        "priority": parent_info["priority"],
                        "state": parent_info["state"],
                        "children": [],
                    }

                mapping["epics"][parent_issue]["children"].append(
                    {
                        "gh_number": gh_number,
                        "title": info["title"],
                        "type": info["type"],
                        "priority": info["priority"],
                        "state": info["state"],
                    }
                )
            else:
                mapping["orphans"].append(info)
        else:
            # No parent - could be top-level epic or standalone issue
            if info["type"] == "epic":
                if gh_number not in mapping["epics"]:
                    mapping["epics"][gh_number] = {
                        "title": info["title"],
                        "type": info["type"],
                        "priority": info["priority"],
                        "state": info["state"],
                        "children": [],
                    }
            else:
                mapping["orphans"].append(info)

    return mapping


def print_mapping_summary(mapping: dict[str, Any]) -> None:
    """Print human-readable summary of mapping."""
    print(f"\n{'=' * 70}")
    print("GitHub Issues → Beads Mapping Analysis")
    print(f"{'=' * 70}\n")

    print(f"Total Issues: {mapping['total_issues']}")
    print(f"  Open:   {mapping['open_issues']}")
    print(f"  Closed: {mapping['closed_issues']}")

    print("\nIssue Types:")
    for itype, count in sorted(mapping["type_counts"].items()):
        print(f"  {itype:12} {count:3}")

    print("\nPriorities:")
    for priority in ["P0", "P1", "P2", "P3", "P4"]:
        count = mapping["priority_counts"].get(priority, 0)
        if count > 0:
            print(f"  {priority}: {count}")

    print(f"\nEpics with Children: {len(mapping['epics'])}")
    for gh_num, epic in sorted(mapping["epics"].items())[:10]:
        status = "✅" if epic["state"] == "CLOSED" else "🔄"
        print(f"  {status} #{gh_num:3} {epic['title'][:50]:50} ({len(epic['children'])} children)")
        if len(epic["children"]) <= 5:
            for child in epic["children"]:
                child_status = "✅" if child["state"] == "CLOSED" else "🔄"
                print(f"      {child_status} #{child['gh_number']:3} {child['title'][:45]}")

    if len(mapping["epics"]) > 10:
        print(f"  ... and {len(mapping['epics']) - 10} more epics")

    print(f"\nOrphan Issues (no parent): {len(mapping['orphans'])}")
    for orphan in mapping["orphans"][:5]:
        status = "✅" if orphan["state"] == "CLOSED" else "🔄"
        print(f"  {status} #{orphan['gh_number']:3} [{orphan['type']:8}] {orphan['title'][:45]}")

    if len(mapping["orphans"]) > 5:
        print(f"  ... and {len(mapping['orphans']) - 5} more orphans")

    print(f"\n{'=' * 70}\n")


def save_mapping(mapping: dict[str, Any], output_file: Path) -> None:
    """Save mapping to JSON for migration script."""
    with open(output_file, "w") as f:
        json.dump(mapping, f, indent=2)
    print(f"Mapping saved to: {output_file}")


def main() -> int:
    """Main entry point."""
    # Find most recent export
    scripts_dir = Path(__file__).parent
    exports = sorted(scripts_dir.glob("github_issues_export_*.json"))

    if not exports:
        print("Error: No GitHub issues export found in scripts/")
        return 1

    latest_export = exports[-1]
    print(f"Analyzing: {latest_export.name}")

    # Analyze and create mapping
    mapping = analyze_issues(latest_export)

    # Print summary
    print_mapping_summary(mapping)

    # Save mapping for next step
    output_file = scripts_dir / "beads_migration_mapping.json"
    save_mapping(mapping, output_file)

    print("\nNext steps:")
    print("  1. Review the mapping above")
    print("  2. Run T095.3 migration script to create beads issues")
    print("  3. Beads will assign new IDs but preserve parent-child relationships")

    return 0


if __name__ == "__main__":
    exit(main())
