#!/usr/bin/env python3
"""Count Matter peers whose connectivity probe failed for over 30 minutes."""

import re
import sys
from datetime import datetime, timedelta

THRESHOLD = timedelta(minutes=30)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
EVENT_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+.*(@\d+:[0-9a-f]+)", re.I
)


def count_stuck(lines, now=None):
    nodes = {}
    last_ts = None
    for line in lines:
        line = ANSI_RE.sub("", line)
        match = EVENT_RE.search(line)
        if not match:
            continue
        timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        peer = match.group(2).lower()
        last_ts = timestamp
        message = line.lower()
        if "all probes failed" in message or (
            "subscription" in message
            and ("subscription failed" in message or "unable to subscribe" in message)
        ):
            nodes.setdefault(peer, ("failed", timestamp))
        elif "subscription successful" in message or "subscription succeeded" in message:
            nodes[peer] = ("ok", timestamp)

    now = now or last_ts or datetime.now()
    return sum(
        status == "failed" and now - failed_at > THRESHOLD
        for status, failed_at in nodes.values()
    )


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sample = [
            "2026-08-05 10:00:00.000 INFO Peer @1:6 All probes failed",
            "2026-08-05 10:40:01.000 INFO Subscription successful @1:7",
        ]
        assert count_stuck(sample, datetime(2026, 8, 5, 10, 40, 1)) == 1
        sample.append("2026-08-05 10:40:02.000 INFO Subscription successful @1:6")
        assert count_stuck(sample, datetime(2026, 8, 5, 11, 11)) == 0
    else:
        print(count_stuck(sys.stdin))
