"""
CLI Command: Replay Risk Runs
Verifies reproducibility of risk runs by re-executing them.
"""
import argparse
import sys
import json
from typing import List

from app.database import SessionLocal
from app.core.risk_runs.replay import RiskRunReplayer, ReplayResult
from app.repositories.risk_run_repository import RiskRunRepository


def format_result(result: ReplayResult) -> str:
    """
    Format replay result for display.

    Args:
        result: ReplayResult instance

    Returns:
        Formatted string
    """
    lines = [
        f"Run ID: {result.run_id}",
        f"Matches: {'✓ YES' if result.matches else '✗ NO'}",
        f"Original Hash: {result.original_hash[:16]}..." if result.original_hash else "Original Hash: N/A",
        f"Replay Hash: {result.replay_hash[:16]}..." if result.replay_hash else "Replay Hash: N/A",
    ]

    if result.error:
        lines.append(f"Error: {result.error}")

    if result.replay_duration_seconds:
        lines.append(f"Duration: {result.replay_duration_seconds:.2f}s")

    if result.diff_summary:
        lines.append("\nDiff Summary:")
        diff = result.diff_summary
        if diff.get("added_keys"):
            lines.append(f"  Added keys: {', '.join(diff['added_keys'][:5])}")
            if len(diff["added_keys"]) > 5:
                lines.append(f"    ... and {len(diff['added_keys']) - 5} more")
        if diff.get("removed_keys"):
            lines.append(f"  Removed keys: {', '.join(diff['removed_keys'][:5])}")
            if len(diff["removed_keys"]) > 5:
                lines.append(f"    ... and {len(diff['removed_keys']) - 5} more")
        if diff.get("changed_keys"):
            lines.append(f"  Changed keys: {', '.join(diff['changed_keys'][:5])}")
            if len(diff["changed_keys"]) > 5:
                lines.append(f"    ... and {len(diff['changed_keys']) - 5} more")
        if diff.get("sample_diffs"):
            lines.append("\n  Sample differences:")
            for sample in diff["sample_diffs"][:3]:
                lines.append(f"    {sample['key']}:")
                lines.append(f"      Original: {str(sample['original'])[:100]}")
                lines.append(f"      Replay: {str(sample['replay'])[:100]}")

    return "\n".join(lines)


def replay_single_run(run_id: str, output_json: bool = False) -> int:
    """
    Replay a single run.

    Args:
        run_id: Run ID (UUID string)
        output_json: Whether to output JSON format

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    db = SessionLocal()
    try:
        replayer = RiskRunReplayer(db)
        result = replayer.replay(run_id)

        if output_json:
            output = {
                "run_id": result.run_id,
                "matches": result.matches,
                "original_hash": result.original_hash,
                "replay_hash": result.replay_hash,
                "diff_summary": result.diff_summary,
                "error": result.error,
                "replay_duration_seconds": result.replay_duration_seconds,
            }
            print(json.dumps(output, indent=2))
        else:
            print(format_result(result))

        return 0 if result.matches else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


def replay_assessment_runs(assessment_id: str, output_json: bool = False) -> int:
    """
    Replay all runs for an assessment.

    Args:
        assessment_id: Assessment ID (ULID string)
        output_json: Whether to output JSON format

    Returns:
        Exit code (0 if all match, 1 if any mismatch)
    """
    db = SessionLocal()
    try:
        repository = RiskRunRepository(db)
        replayer = RiskRunReplayer(db)

        # Get all runs for assessment (need tenant_id, but we'll query directly)
        runs = db.query(RiskRun).filter(
            RiskRun.assessment_id == assessment_id
        ).all()

        if not runs:
            print(f"No runs found for assessment {assessment_id}", file=sys.stderr)
            return 1

        # Replay each run
        results: List[ReplayResult] = []
        for run in runs:
            result = replayer.replay(run.id)
            results.append(result)

        if output_json:
            output = {
                "assessment_id": assessment_id,
                "total_runs": len(results),
                "matches": sum(1 for r in results if r.matches),
                "mismatches": sum(1 for r in results if not r.matches),
                "results": [
                    {
                        "run_id": r.run_id,
                        "matches": r.matches,
                        "original_hash": r.original_hash,
                        "replay_hash": r.replay_hash,
                        "error": r.error,
                    }
                    for r in results
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Assessment: {assessment_id}")
            print(f"Total runs: {len(results)}")
            print(f"Matches: {sum(1 for r in results if r.matches)}")
            print(f"Mismatches: {sum(1 for r in results if not r.matches)}")
            print("\n" + "=" * 80 + "\n")
            for result in results:
                print(format_result(result))
                print("\n" + "-" * 80 + "\n")

        # Return 0 if all match, 1 if any mismatch
        return 0 if all(r.matches for r in results) else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Replay risk runs to verify reproducibility"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="UUID of a specific run to replay",
    )
    parser.add_argument(
        "--assessment-id",
        type=str,
        help="ULID of an assessment (use with --all-runs)",
    )
    parser.add_argument(
        "--all-runs",
        action="store_true",
        help="Replay all runs for the assessment (requires --assessment-id)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.run_id and args.assessment_id:
        print("Error: Cannot specify both --run-id and --assessment-id", file=sys.stderr)
        return 1

    if args.all_runs and not args.assessment_id:
        print("Error: --all-runs requires --assessment-id", file=sys.stderr)
        return 1

    if not args.run_id and not args.assessment_id:
        print("Error: Must specify either --run-id or --assessment-id", file=sys.stderr)
        parser.print_help()
        return 1

    # Execute command
    if args.run_id:
        return replay_single_run(args.run_id, output_json=args.json)
    elif args.assessment_id:
        if args.all_runs:
            return replay_assessment_runs(args.assessment_id, output_json=args.json)
        else:
            print("Error: --assessment-id requires --all-runs", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
