#!/usr/bin/env python3
"""Export GitHub issues to JSON and CSV for beads migration.

This script uses the GitHub CLI to export all issues (open and closed)
with their metadata, comments, and history.
"""

import csv
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def run_gh_command(args: list[str]) -> Any:
    """Run a gh CLI command and return parsed JSON output."""
    try:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running gh command: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}", file=sys.stderr)
        sys.exit(1)


def get_issue_comments(issue_number: int) -> list[dict]:
    """Get all comments for a specific issue."""
    return run_gh_command(
        [
            "issue",
            "view",
            str(issue_number),
            "--json",
            "comments",
        ]
    ).get("comments", [])


def export_issues() -> tuple[list[dict], list[dict]]:
    """Export all issues (open and closed) with full metadata."""
    print("Fetching open issues...")
    open_issues = run_gh_command(
        [
            "issue",
            "list",
            "--state",
            "open",
            "--limit",
            "1000",
            "--json",
            "number,title,body,labels,milestone,assignees,author,createdAt,updatedAt,state,url",
        ]
    )

    print(f"Found {len(open_issues)} open issues")

    print("Fetching closed issues...")
    closed_issues = run_gh_command(
        [
            "issue",
            "list",
            "--state",
            "closed",
            "--limit",
            "1000",
            "--json",
            "number,title,body,labels,milestone,assignees,author,createdAt,updatedAt,closedAt,state,url",
        ]
    )

    print(f"Found {len(closed_issues)} closed issues")

    all_issues = open_issues + closed_issues
    print(f"Total: {len(all_issues)} issues")

    # Fetch comments for each issue
    print("\nFetching comments for each issue...")
    for i, issue in enumerate(all_issues, 1):
        issue_number = issue["number"]
        print(f"  [{i}/{len(all_issues)}] Issue #{issue_number}", end="\r")

        comments_data = get_issue_comments(issue_number)
        issue["comments"] = comments_data
        issue["comment_count"] = len(comments_data)

    print("\n\nCompleted fetching all issue data")
    return all_issues, open_issues


def save_json_export(issues: list[dict], output_dir: Path) -> Path:
    """Save issues to JSON format."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"github_issues_export_{timestamp}.json"

    export_data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "total_issues": len(issues),
        "issues": issues,
    }

    with output_file.open("w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\n✓ JSON export saved to: {output_file}")
    return output_file


def save_csv_export(issues: list[dict], output_dir: Path) -> Path:
    """Save issues to CSV format (flattened data without comments)."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"github_issues_export_{timestamp}.csv"

    # Define CSV columns
    fieldnames = [
        "number",
        "title",
        "state",
        "url",
        "author",
        "created_at",
        "updated_at",
        "closed_at",
        "labels",
        "milestone",
        "assignees",
        "comment_count",
        "body_preview",
    ]

    with output_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for issue in issues:
            # Flatten nested structures for CSV
            labels = ", ".join([label["name"] for label in issue.get("labels", [])])
            assignees = ", ".join([a["login"] for a in issue.get("assignees", [])])
            milestone = issue.get("milestone", {}).get("title", "") if issue.get("milestone") else ""
            author = issue.get("author", {}).get("login", "")
            body = issue.get("body", "") or ""
            body_preview = body[:100].replace("\n", " ") + ("..." if len(body) > 100 else "")

            writer.writerow(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "url": issue["url"],
                    "author": author,
                    "created_at": issue.get("createdAt", ""),
                    "updated_at": issue.get("updatedAt", ""),
                    "closed_at": issue.get("closedAt", ""),
                    "labels": labels,
                    "milestone": milestone,
                    "assignees": assignees,
                    "comment_count": issue.get("comment_count", 0),
                    "body_preview": body_preview,
                }
            )

    print(f"✓ CSV export saved to: {output_file}")
    return output_file


def print_summary(issues: list[dict]) -> None:
    """Print summary statistics about the exported issues."""
    open_count = sum(1 for i in issues if i["state"] == "OPEN")
    closed_count = sum(1 for i in issues if i["state"] == "CLOSED")

    # Count labels
    label_counts: dict[str, int] = {}
    for issue in issues:
        for label in issue.get("labels", []):
            label_name = label["name"]
            label_counts[label_name] = label_counts.get(label_name, 0) + 1

    print("\n" + "=" * 60)
    print("EXPORT SUMMARY")
    print("=" * 60)
    print(f"Total issues: {len(issues)}")
    print(f"  Open: {open_count}")
    print(f"  Closed: {closed_count}")
    print("\nLabel distribution:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {label}: {count}")
    print("=" * 60)


def main() -> None:
    """Main entry point for issue export script."""
    print("=" * 60)
    print("GitHub Issues Export Script")
    print("=" * 60)
    print()

    # Ensure scripts directory exists
    script_dir = Path(__file__).parent
    script_dir.mkdir(exist_ok=True)

    # Export issues
    all_issues, _ = export_issues()

    # Save to both formats
    json_file = save_json_export(all_issues, script_dir)
    csv_file = save_csv_export(all_issues, script_dir)

    # Print summary
    print_summary(all_issues)

    print("\n✓ Export complete!")
    print(f"  JSON: {json_file}")
    print(f"  CSV: {csv_file}")


if __name__ == "__main__":
    main()
