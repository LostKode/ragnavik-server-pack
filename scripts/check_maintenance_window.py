#!/usr/bin/env python3
"""Allow production deployment only inside a release train's local window."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("train", type=Path)
    parser.add_argument("--at", help="ISO timestamp used by tests; defaults to now")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    train = json.loads(args.train.read_text(encoding="utf-8"))
    window = train["deployment_window"]
    timezone = ZoneInfo(window["timezone"])
    now = dt.datetime.fromisoformat(args.at) if args.at else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise SystemExit("--at must include a UTC offset")
    local_now = now.astimezone(timezone)
    hour, minute = (int(value) for value in window["start"].split(":"))
    start = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    end = start + dt.timedelta(minutes=window["duration_minutes"])
    inside = start <= local_now < end
    if local_now >= end:
        next_start = start + dt.timedelta(days=1)
    elif local_now < start:
        next_start = start
    else:
        next_start = start
    state = "OPEN" if inside else "CLOSED"
    print(
        f"maintenance window {state}; local time {local_now.isoformat()}; "
        f"window {start.isoformat()} to {end.isoformat()}; next start {next_start.isoformat()}"
    )
    if not inside and not args.report_only:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
