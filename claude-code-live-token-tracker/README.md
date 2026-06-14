# Claude Code Live Token / Context Status Line

A small Python script that shows your **model**, **live context-window usage**, and
**session cost** at the bottom of the Claude Code terminal — updated as you work.

Example output:

```
Opus 4.8 | ctx 99.3k/1m (10%) | $0.1234
```

| Segment            | Meaning                                                            |
|--------------------|-------------------------------------------------------------------|
| `Opus 4.8`         | Current model display name                                         |
| `ctx 99.3k/1m (10%)` | Input-side tokens currently in the context window / the 1M limit  |
| `$0.1234`          | Total USD cost of the current session                             |

The context segment is **color-coded**: green < 60%, yellow 60–85%, red ≥ 85%.

---

## Where it shows up

It renders as the **status line** — the single line pinned at the **bottom of the
Claude Code TUI**, just under the prompt input box. It is **not** a chat message;
it persists and refreshes in place every turn. (It does not appear in the web app,
only in the terminal / IDE TUI.)

---

## How it works

Claude Code calls the configured `statusLine.command` on every render and pipes a
small JSON blob into the command's **stdin**, including:

- `model.display_name` — current model
- `cost.total_cost_usd` — running session cost
- `transcript_path` — path to the session's JSONL transcript

`statusline.py`:

1. Reads that JSON from stdin.
2. Opens the transcript JSONL and scans **from the end** for the most recent
   assistant message that carries a `usage` block.
3. Sums `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`
   — that total is what actually occupies the context window.
4. Prints `model | ctx used/limit (pct) | $cost`.

> **⚠️ The context window is hardcoded.** `CONTEXT_LIMIT` is fixed at
> `1_000_000` (the 1M window) near the top of `statusline.py`. The script does
> **not** auto-detect the model's actual window — if your model has a different
> limit (e.g. 200k), the percentage will be wrong until you edit that constant.
> Change it manually to match whatever model you run:
>
> ```python
> CONTEXT_LIMIT = 1_000_000  # context window (1M) — edit if your model differs
> ```

---

## Setup (Windows)

> These files are a **copy for reference**. Claude Code reads the script from your
> global config dir, so install by copying them there.

1. **Copy the script** to your Claude config directory:

   ```powershell
   Copy-Item .\tools\statusline\statusline.py "$env:USERPROFILE\.claude\statusline.py"
   ```

2. **Register it** in `~/.claude/settings.json` by adding the `statusLine` block
   (see `settings.snippet.json` in this folder). Merge it into your existing
   settings — keep your other keys (`model`, `theme`, `hooks`, …):

   ```json
   "statusLine": {
     "type": "command",
     "command": "python C:/Users/sachu/.claude/statusline.py"
   }
   ```

   > Requires `python` on your PATH. Verify with `python --version`.
   > On macOS/Linux use `python3` and a `~/.claude/...` path.

3. **Restart Claude Code.** The status line appears at the bottom of the TUI.

---

## Files in this folder

| File                     | Purpose                                              |
|--------------------------|------------------------------------------------------|
| `statusline.py`          | The status-line script (reads stdin JSON + transcript) |
| `settings.snippet.json`  | The `statusLine` block to merge into `settings.json` |
| `README.md`              | This file                                            |

---

## Troubleshooting

- **Nothing shows up** → confirm `python` resolves on PATH, and that the path in
  `settings.json` points at the copied script. Restart Claude Code after editing.
- **Percentage looks wrong** → check `CONTEXT_LIMIT` matches your model's window.
- **`ctx` segment missing** → the transcript had no `usage` block yet (e.g. very
  first turn); it appears after the first assistant response.
