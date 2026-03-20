"""
agent.py — Log Monitoring Agent (with smart grouping)
------------------------------------------------------
A minimal but real AI agent that:
  1. PERCEIVES  — reads and parses log lines
  2. DETECTS    — flags WARNING / ERROR / CRITICAL entries
  3. GROUPS     — clusters similar errors by fingerprint pattern
  4. DECIDES    — 1 LLM call per group, not per log line
  5. ACTS       — writes 1 incident ticket per group (with occurrence count)
  6. REFLECTS   — skips groups already ticketed this run

Requirements:
    pip install openai

Usage:
    export AZURE_OPENAI_KEY=your-azure-key-here
    export AZURE_ENDPOINT=your-endpoint-here
    python sample_log_generator.py   # create sample logs
    python agent.py                  # run the agent
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

LOG_FILE = "app.log"
INCIDENTS_FILE = "incidents.json"

# Azure OpenAI settings
AZURE_ENDPOINT    =  os.environ.get("AZURE_ENDPOINT")
AZURE_DEPLOYMENT  = "gpt-4o-mini"
AZURE_API_VERSION = "2024-12-01-preview"

# Only lines with these levels will be analysed by the LLM
LEVELS_TO_WATCH = {"WARNING", "ERROR", "CRITICAL"}

# Regex to parse a log line
LOG_PATTERN = re.compile(
    r"\[(?P<timestamp>.+?)\] \[(?P<level>\w+)\] (?P<message>.+)"
)

# Patterns to strip from log messages to create a fingerprint.
# user IDs, numbers, IPs, emails, UUIDs → replaced with a placeholder.
DYNAMIC_PATTERNS = [
    (re.compile(r"user_\d+"),                      "<user>"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.\w+\b"),      "<email>"),
    (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b"),     "<ip>"),
    (re.compile(r"\b[0-9a-f-]{36}\b"),              "<uuid>"),
    (re.compile(r"\b\d+ms\b"),                      "<Nms>"),
    (re.compile(r"\b\d+%\b"),                       "<N%>"),
    (re.compile(r"\b\d+\b"),                        "<N>"),
]

# ─── Azure OpenAI client ──────────────────────────────────────────────────────

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=os.environ.get("AZURE_OPENAI_KEY"),
    api_version=AZURE_API_VERSION,
)

# ─── Data structures ──────────────────────────────────────────────────────────


def load_incidents() -> list[dict]:
    """Load existing incidents from JSON file."""
    if Path(INCIDENTS_FILE).exists():
        with open(INCIDENTS_FILE) as f:
            return json.load(f)
    return []


def save_incidents(incidents: list[dict]):
    """Persist all incidents to JSON file."""
    with open(INCIDENTS_FILE, "w") as f:
        json.dump(incidents, f, indent=2)


# ─── Step 1: PERCEIVE — Read & parse logs ────────────────────────────────────


def read_logs(filepath: str) -> list[dict]:
    """
    Parse the log file into structured entries.
    Returns only lines that match our watched severity levels.
    """
    entries = []
    with open(filepath) as f:
        for line in f:
            match = LOG_PATTERN.match(line.strip())
            if match:
                entry = match.groupdict()
                if entry["level"] in LEVELS_TO_WATCH:
                    entries.append(entry)
    return entries


# ─── Step 2: GROUP — Fingerprint and cluster similar errors ──────────────────


def fingerprint(message: str) -> str:
    """
    Strip dynamic values (user IDs, numbers, IPs) from a log message
    to produce a stable pattern key.

    e.g. Both of these produce the same fingerprint:
      "Failed to send email to user_1111: SMTP connection refused"
      "Failed to send email to user_4544: SMTP connection refused"
    →   "Failed to send email to <user>: SMTP connection refused"
    """
    fp = message
    for pattern, placeholder in DYNAMIC_PATTERNS:
        fp = pattern.sub(placeholder, fp)
    return fp.strip()


def group_entries(entries: list[dict]) -> dict[str, list[dict]]:
    """
    Group log entries by their fingerprint.
    Returns a dict: { fingerprint_key: [entry, entry, ...] }
    """
    groups = defaultdict(list)
    for entry in entries:
        key = fingerprint(entry["message"])
        groups[key].append(entry)
    return dict(groups)


def filter_new_groups(
    groups: dict[str, list[dict]],
    existing_incidents: list[dict]
) -> dict[str, list[dict]]:
    """
    Remove groups whose fingerprint already has an open incident.
    Dedup is now fingerprint-based, not message-based.
    """
    existing_fingerprints = {inc.get("fingerprint", "") for inc in existing_incidents}
    return {
        fp: entries
        for fp, entries in groups.items()
        if fp not in existing_fingerprints
    }


# ─── Step 3: DECIDE — LLM analyses one group ─────────────────────────────────


def analyse_group_with_llm(fp: str, entries: list[dict]) -> tuple[dict, dict]:
    """
    Send the error pattern + occurrence count to the LLM.
    Uses the fingerprint (not a raw message) so the LLM sees the
    generalised pattern, not one specific user ID.

    Returns (analysis dict, token_usage dict).
    """
    # Pick the most severe level seen in the group
    level_priority = {"CRITICAL": 3, "ERROR": 2, "WARNING": 1}
    representative_level = max(
        entries, key=lambda e: level_priority.get(e["level"], 0)
    )["level"]

    # Use first and last timestamps to show the time window
    timestamps = [e["timestamp"] for e in entries]
    time_range = f"{timestamps[0]}  →  {timestamps[-1]}" if len(timestamps) > 1 else timestamps[0]

    prompt = f"""
You are an expert Site Reliability Engineer analysing grouped application logs.

Multiple log entries have been grouped under the same error pattern:

  Pattern      : {fp}
  Level        : {representative_level}
  Occurrences  : {len(entries)}
  Time range   : {time_range}
  Sample log   : {entries[0]['message']}

Respond ONLY with a valid JSON object with these exact keys:
{{
  "severity": "WARNING" | "ERROR" | "CRITICAL",
  "root_cause": "<one sentence explaining the likely cause>",
  "recommended_action": "<one sentence — most important thing to do now>"
}}
"""

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    usage = {
        "prompt_tokens":     response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens":      response.usage.total_tokens,
    }

    return json.loads(response.choices[0].message.content), usage


# ─── Step 4: ACT — Create one incident per group ─────────────────────────────


def create_group_incident(
    fp: str,
    entries: list[dict],
    analysis: dict
) -> dict:
    """
    Build a single incident ticket for the entire group.
    Includes occurrence count and one sample log for reference.
    """
    return {
        "id": f"INC-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}",
        "created_at": datetime.now().isoformat(),
        "fingerprint": fp,
        "occurrence_count": len(entries),
        "first_seen": entries[0]["timestamp"],
        "last_seen": entries[-1]["timestamp"],
        "log_level": entries[0]["level"],
        "sample_log": entries[0]["message"],      # one reference log only
        "all_messages": [e["message"] for e in entries],
        "severity": analysis["severity"],
        "root_cause": analysis["root_cause"],
        "recommended_action": analysis["recommended_action"],
        "status": "open",
    }


# ─── Step 5: REFLECT — Print a run summary ───────────────────────────────────


def print_summary(new_incidents: list[dict], total_raw_logs: int):
    if not new_incidents:
        print("\n✅ No new incidents found this run.\n")
        return

    total_occurrences = sum(inc["occurrence_count"] for inc in new_incidents)
    print(f"\n{'='*60}")
    print(f"  🚨 {len(new_incidents)} INCIDENT(S) from {total_occurrences} log lines")
    print(f"{'='*60}")
    for inc in new_incidents:
        icon = "🔴" if inc["severity"] == "CRITICAL" else "🟠" if inc["severity"] == "ERROR" else "🟡"
        count = inc["occurrence_count"]
        print(f"\n{icon} [{inc['severity']}] {inc['id']}  (x{count} occurrences)")
        print(f"   Pattern : {inc['fingerprint']}")
        print(f"   Sample  : {inc['sample_log']}")
        print(f"   Window  : {inc['first_seen']}  →  {inc['last_seen']}")
        print(f"   Cause   : {inc['root_cause']}")
        print(f"   Action  : {inc['recommended_action']}")
    print(f"\n📄 All incidents saved to → {INCIDENTS_FILE}\n")


# ─── Main agent loop ─────────────────────────────────────────────────────────


def run_agent():
    print("\n🤖 Log Monitoring Agent starting...\n")

    # PERCEIVE
    print(f"📂 Reading logs from: {LOG_FILE}")
    entries = read_logs(LOG_FILE)
    print(f"   Found {len(entries)} flagged log lines (WARNING/ERROR/CRITICAL)")

    # GROUP — cluster by fingerprint
    groups = group_entries(entries)
    print(f"   Grouped into {len(groups)} distinct error pattern(s)")
    for fp, grp in groups.items():
        print(f"   • [{len(grp):>2}x]  {fp[:70]}")

    # REFLECT — skip groups already ticketed
    existing_incidents = load_incidents()
    new_groups = filter_new_groups(groups, existing_incidents)
    print(f"\n   {len(new_groups)} new group(s) not yet ticketed")

    if not new_groups:
        print_summary([], len(entries))
        return

    # DECIDE + ACT — one LLM call per group
    new_incidents = []
    total_prompt_tokens     = 0
    total_completion_tokens = 0
    total_tokens            = 0

    for i, (fp, grp_entries) in enumerate(new_groups.items(), 1):
        print(f"\n🔍 Analysing group [{i}/{len(new_groups)}]  "
              f"({len(grp_entries)}x): {fp[:55]}...")

        try:
            analysis, usage = analyse_group_with_llm(fp, grp_entries)  # DECIDE
            incident = create_group_incident(fp, grp_entries, analysis)  # ACT
            new_incidents.append(incident)

            print(f"   🪙 Tokens — prompt: {usage['prompt_tokens']}  "
                  f"completion: {usage['completion_tokens']}  "
                  f"total: {usage['total_tokens']}")

            total_prompt_tokens     += usage["prompt_tokens"]
            total_completion_tokens += usage["completion_tokens"]
            total_tokens            += usage["total_tokens"]

        except Exception as e:
            print(f"   ⚠️  Skipped due to error: {e}")

    # Persist
    all_incidents = existing_incidents + new_incidents
    save_incidents(all_incidents)

    # Token summary
    if new_incidents:
        print(f"\n{'─'*60}")
        print(f"  📊 TOKEN USAGE  ({len(new_incidents)} LLM call(s) for "
              f"{len(entries)} log lines)")
        print(f"{'─'*60}")
        print(f"   Prompt tokens     : {total_prompt_tokens}")
        print(f"   Completion tokens : {total_completion_tokens}")
        print(f"   Total tokens      : {total_tokens}")
        print(f"{'─'*60}")

    # REFLECT
    print_summary(new_incidents, len(entries))


if __name__ == "__main__":
    run_agent()
