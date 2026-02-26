#!/usr/bin/env python3
"""Count Matter nodes stuck in failed state for >30 minutes.

Reads Matter Server logs from stdin (piped from supervisor API).
Tracks subscription failure/success events per node. Only counts
nodes whose last event is a failure older than the threshold,
indicating they haven't self-recovered and likely need a server restart.

Normal Thread mesh jitter (fail then recover in <5 min) is ignored.
"""

import re
import sys
from datetime import datetime, timedelta

THRESHOLD = timedelta(minutes=30)

# ANSI escape code pattern for stripping color codes from log output
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
EVENT_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+.*<Node:(\d+)>"
)

nodes: dict[str, tuple[str, datetime]] = {}
last_ts = None

for line in sys.stdin:
    line = ANSI_RE.sub("", line)
    m = EVENT_RE.search(line)
    if not m:
        continue

    ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    node = m.group(2)
    last_ts = ts

    if "Subscription failed" in line or "Unable to subscribe" in line:
        # Only record the first failure timestamp (don't update on retries)
        if node not in nodes or nodes[node][0] != "failed":
            nodes[node] = ("failed", ts)
    elif "Subscription succeeded" in line or "Re-Subscription succeeded" in line:
        nodes[node] = ("ok", ts)

now = last_ts or datetime.now()
stuck = sum(
    1
    for status, fail_ts in nodes.values()
    if status == "failed" and (now - fail_ts) > THRESHOLD
)
print(stuck)
