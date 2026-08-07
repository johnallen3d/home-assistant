#!/usr/bin/env python3
"""Report Matter peers/entities stuck in failed state."""

import json
import re
import sys
from datetime import datetime, timezone, timedelta

THRESHOLD = timedelta(minutes=30)
MARKER = "__HA_STATES__"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
PEER_RE = re.compile(r"(@\d+:[0-9a-f]+)", re.I)
FULL_TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2})[ T](\d{2})[: ](\d{2}):(\d{2})\.\d+")
TIME_RE = re.compile(r"^(\d{2})[: ](\d{2}):(\d{2})\.\d+")


def as_utc(value):
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_timestamp(line, current_date):
    match = FULL_TS_RE.search(line)
    if match:
        date, hour, minute, second = match.groups()
        return as_utc(f"{date} {hour}:{minute}:{second}+00:00"), date

    match = TIME_RE.search(line)
    if match and current_date:
        hour, minute, second = match.groups()
        return as_utc(f"{current_date} {hour}:{minute}:{second}+00:00"), current_date

    return None, current_date


def matter_entry_ids(path="/config/.storage/core.config_entries"):
    try:
        with open(path) as f:
            entries = json.load(f)["data"]["entries"]
    except Exception:
        return set()
    return {entry["entry_id"] for entry in entries if entry.get("domain") == "matter"}


def entity_devices(path="/config/.storage/core.entity_registry"):
    try:
        with open(path) as f:
            entities = json.load(f)["data"]["entities"]
    except Exception:
        return {}
    matter_ids = matter_entry_ids()
    return {
        entity["entity_id"]: entity.get("device_id") or entity["entity_id"]
        for entity in entities
        if entity.get("config_entry_id") in matter_ids
    }


def device_names(path="/config/.storage/core.device_registry"):
    try:
        with open(path) as f:
            devices = json.load(f)["data"]["devices"]
    except Exception:
        return {}
    return {
        device["id"]: device.get("name_by_user") or device.get("name") or device["id"]
        for device in devices
    }


def split_input(lines):
    text = "".join(lines)
    if MARKER not in text:
        return text.splitlines(), []
    log_text, states_text = text.split(MARKER, 1)
    try:
        states = json.loads(states_text.strip())
    except json.JSONDecodeError:
        states = []
    return log_text.splitlines(), states


def add_log_nodes(nodes, lines):
    current_date = None
    last_ts = None
    for line in lines:
        line = ANSI_RE.sub("", line).strip()
        timestamp, current_date = parse_timestamp(line, current_date)
        peer_match = PEER_RE.search(line)
        if not timestamp or not peer_match:
            continue

        last_ts = timestamp
        peer = peer_match.group(1).lower()
        message = line.lower()
        failed = "all probes failed" in message or (
            "subscription" in message
            and ("failed" in message or "unable to subscribe" in message or "timed out" in message or "after loss" in message)
        )
        recovered = (
            ("probe" in message and "success" in message)
            or "subscription successful" in message
            or "subscription succeeded" in message
        )

        if failed:
            nodes[peer] = {"peer": peer, "name": peer, "status": "failed", "failed_at": timestamp, "source": "matter_log", "threshold": THRESHOLD}
        elif recovered:
            nodes[peer] = {"peer": peer, "name": peer, "status": "ok", "failed_at": timestamp, "source": "matter_log", "threshold": THRESHOLD}
    return last_ts


def add_unavailable_nodes(nodes, states):
    entity_to_device = entity_devices()
    names = device_names()
    for state in states:
        entity_id = state.get("entity_id")
        if state.get("state") not in ("unavailable", "unknown") or entity_id not in entity_to_device:
            continue
        device_id = entity_to_device[entity_id]
        changed = as_utc(state["last_changed"])
        node = nodes.get(device_id)
        if not node or changed < node["failed_at"]:
            nodes[device_id] = {
                "peer": device_id,
                "name": names.get(device_id, entity_id),
                "status": "failed",
                "failed_at": changed,
                "source": "ha_unavailable",
                "threshold": timedelta(0),
            }


def stuck_nodes(lines, now=None):
    log_lines, states = split_input(lines)
    nodes = {}
    last_ts = add_log_nodes(nodes, log_lines)
    add_unavailable_nodes(nodes, states)
    now = as_utc(now or last_ts or datetime.now(timezone.utc))
    stuck = [
        {
            "peer": node["peer"],
            "name": node["name"],
            "source": node["source"],
            "failed_at": node["failed_at"].isoformat(timespec="seconds"),
            "age_minutes": int((now - node["failed_at"]).total_seconds() // 60),
        }
        for node in nodes.values()
        if node["status"] == "failed" and now - node["failed_at"] >= node["threshold"]
    ]
    return sorted(stuck, key=lambda node: node["failed_at"])


def report(lines, now=None):
    nodes = stuck_nodes(lines, now)
    first = nodes[0] if nodes else {}
    return {"count": len(nodes), "nodes": nodes, "first_node": first.get("name", ""), "oldest_age_minutes": first.get("age_minutes", 0)}


def count_stuck(lines, now=None):
    return report(lines, now)["count"]


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sample = [
            "2026-08-05 10:00:00.000 INFO Peer @1:6 All probes failed\n",
            "2026-08-05 10:40:01.000 INFO Subscription successful @1:6\n",
            "2026-08-05 10:40:02.000 INFO Subscription 123 peer @1:6 timed out\n",
        ]
        result = report(sample, datetime(2026, 8, 5, 11, 11, tzinfo=timezone.utc))
        assert result["count"] == 1
        assert result["first_node"] == "@1:6"
        assert result["oldest_age_minutes"] == 30

        sample.append("11:11:01.000 INFO ClientInteraction Probe « @1:6•c104 (success)\n")
        assert count_stuck(sample, datetime(2026, 8, 5, 11, 42, tzinfo=timezone.utc)) == 0
    else:
        print(json.dumps(report(sys.stdin)))
