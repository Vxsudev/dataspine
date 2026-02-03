#!/usr/bin/env python3
"""Pipeline runner for dataspine."""

import argparse
import sys
from datetime import datetime


def main() -> int:
    """Main entry point for pipeline runner."""
    parser = argparse.ArgumentParser(description="Run dataspine pipeline")
    
    parser.add_argument(
        "--mode",
        choices=["live", "backfill"],
        required=True,
        help="Pipeline mode: live or backfill"
    )
    parser.add_argument(
        "--client",
        type=str,
        help="Client identifier"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run without executing"
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date for backfill (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date for backfill (YYYY-MM-DD)"
    )
    
    args = parser.parse_args()
    
    # Print what would run
    print(f"Pipeline Configuration:")
    print(f"  Mode: {args.mode}")
    print(f"  Client: {args.client or 'all'}")
    print(f"  Dry Run: {args.dry_run}")
    
    if args.mode == "backfill":
        print(f"  Start Date: {args.start or 'not specified'}")
        print(f"  End Date: {args.end or 'not specified'}")
    
    if args.dry_run:
        print("\n[DRY RUN] No actual operations performed.")
    else:
        print("\n[INFO] Pipeline execution would start here.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
