# 🤖 Log Monitoring Agent

A minimal but production-minded AI agent that reads application logs, groups similar errors by pattern, and uses **Azure OpenAI (GPT-4o-mini)** to classify severity, identify root causes, and generate incident tickets - automatically.

Built as a learning project to understand what makes something an **agent** vs a plain script.

---

## What it does

```
app.log
   ↓
[PERCEIVE]   Parse log lines → filter WARNING / ERROR / CRITICAL
   ↓
[GROUP]      Fingerprint messages → cluster similar errors together
   ↓
[DECIDE]     1 LLM call per group → severity + root cause + action
   ↓
[ACT]        Write 1 incident ticket per group → incidents.json
   ↓
[REFLECT]    Skip groups already ticketed → print token usage summary
```

### Smart grouping — the key feature

Instead of firing one LLM call per log line, the agent **fingerprints** each message by stripping dynamic values (user IDs, IPs, timestamps, numbers), then groups all matching lines under one pattern.

```
"Failed to send email to user_1111: SMTP connection refused"
"Failed to send email to user_4544: SMTP connection refused"
"Failed to send email to user_8823: SMTP connection refused"
                         ↓  all become  ↓
         "Failed to send email to <user>: SMTP connection refused"
                         ↓  one LLM call  ↓
                      1 incident ticket
                      occurrence_count: 3
```

50 SMTP errors → 1 LLM call instead of 50. Fewer tokens, better context, smarter output.

---

## Project structure

```
log-monitoring-agent/
├── agent.py                  # Main agent
├── sample_log_generator.py   # Generates a realistic app.log for testing
├── test_connection.py        # Verifies Azure OpenAI credentials before running
├── requirements.txt
├── app.log                   # Created at runtime
└── incidents.json            # Created by the agent
```

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/sachinkumar579/vibe-coding.git
cd log-monitoring-agent
pip install -r requirements.txt
```

### 2. Set your Azure OpenAI key

```bash
export AZURE_OPENAI_KEY=your-key-here
export AZURE_ENDPOINT=your-endpoint-here
```

### 3. Verify the connection

```bash
python test_connection.py
```

Expected output:
```
✅ Found key: sk-azur**********
✅ Response  : CONNECTION OK
✅ Prompt tokens     : 18
✅ Parsed JSON : {'status': 'ok', 'message': '...'}

✅ All checks passed — agent.py is ready to run!
```

### 4. Generate sample logs

```bash
python sample_log_generator.py
```

### 5. Run the agent

```bash
python agent.py
```

---

## Sample output

```
🤖 Log Monitoring Agent starting...

📂 Reading logs from: app.log
   Found 18 flagged log lines (WARNING/ERROR/CRITICAL)
   Grouped into 4 distinct error pattern(s)
   • [11x]  Failed to send email to <user>: SMTP connection refused
   • [ 4x]  Database connection timeout after <Nms>ms
   • [ 2x]  Memory usage at <N%> — approaching limit
   • [ 1x]  DISK FULL: /var/data has <N> bytes remaining

   4 new group(s) not yet ticketed

🔍 Analysing group [1/4]  (11x): Failed to send email to <user>: SMTP...
   🪙 Tokens — prompt: 182  completion: 54  total: 236

🔍 Analysing group [2/4]  (4x): Database connection timeout after <Nms>ms...
   🪙 Tokens — prompt: 176  completion: 49  total: 225

────────────────────────────────────────────────────────────
  📊 TOKEN USAGE  (4 LLM call(s) for 18 log lines)
────────────────────────────────────────────────────────────
   Prompt tokens     : 698
   Completion tokens : 201
   Total tokens      : 899
────────────────────────────────────────────────────────────

============================================================
  🚨 4 INCIDENT(S) from 18 log lines
============================================================

🔴 [CRITICAL] INC-20241110140712345  (x1 occurrences)
   Pattern : DISK FULL: /var/data has <N> bytes remaining
   Sample  : DISK FULL: /var/data has 0 bytes remaining
   Window  : 2024-11-10 14:07:00  →  2024-11-10 14:07:00
   Cause   : The disk partition /var/data has run out of storage space
   Action  : Free disk space immediately or expand the volume

📄 All incidents saved to → incidents.json
```

---

## incidents.json schema

Each incident ticket looks like this:

```json
{
  "id": "INC-20241110140712345",
  "created_at": "2024-11-10T14:07:12.345678",
  "fingerprint": "Failed to send email to <user>: SMTP connection refused",
  "occurrence_count": 11,
  "first_seen": "2024-11-10 13:52:00",
  "last_seen": "2024-11-10 14:06:00",
  "log_level": "ERROR",
  "sample_log": "Failed to send email to user_1111: SMTP connection refused",
  "severity": "ERROR",
  "root_cause": "The SMTP server is refusing connections, likely due to misconfiguration or service outage",
  "recommended_action": "Check SMTP server status and verify credentials and port configuration",
  "status": "open"
}
```

---

## Configuration

All settings live at the top of `agent.py`:

| Variable | Description |
|---|---|
| `LOG_FILE` | Path to the log file to monitor |
| `INCIDENTS_FILE` | Where to write incident tickets |
| `AZURE_ENDPOINT` | Your Azure OpenAI resource endpoint |
| `AZURE_DEPLOYMENT` | Your deployment name (e.g. `gpt-4o-mini`) |
| `AZURE_API_VERSION` | API version string |
| `LEVELS_TO_WATCH` | Set of log levels to flag (`WARNING`, `ERROR`, `CRITICAL`) |
| `DYNAMIC_PATTERNS` | Regex rules for fingerprinting (extend as needed) |

---

## Extending the agent

**Add real-time monitoring**
Replace `read_logs()` with a file watcher using `watchdog` — run the agent loop every N seconds.

**Add Slack alerts**
After `create_group_incident()`, POST to a Slack webhook for CRITICAL tickets.

**Connect to a real ticketing system**
Replace the JSON write in `save_incidents()` with a call to Jira, PagerDuty, or Linear.

**Add more fingerprint patterns**
Extend `DYNAMIC_PATTERNS` with regex for your specific log format — session tokens, order IDs, trace IDs, etc.

---

## Why this is an agent (not just a script)

A regular script would do:
```python
if "ERROR" in line:
    create_ticket(line)
```

This agent instead asks: *"Given this pattern of errors, what is the likely root cause and what should an engineer do?"* — and gets a reasoned, contextual answer that adapts to the content. The reasoning step is not hardcoded. That's what makes it an agent.

---

## Requirements

- Python 3.10+
- `openai >= 1.30.0`
- Azure OpenAI resource with a `gpt-4o-mini` deployment

---

## License

MIT
