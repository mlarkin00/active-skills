---
type: Runtime Behaviour
resource: skill-creator-enhanced/scripts/propose.py
title: claude -p --output-format json returns an array of messages, not a result object
description: The text lives on `result` of the last message whose type is `result`,
  alongside is_error and total_cost_usd; and stdin must be redirected or every call
  stalls three seconds waiting for input.
tags: [claude-cli, subprocess, evals]
timestamp: '2026-08-06T17:20:00+00:00'
---

`claude -p ... --output-format json` emits a JSON **array**, not an object. The
natural-looking `json.loads(stdout)["result"]` raises `TypeError`.

Observed shape, Claude Code 2.1.x, 2026-08-06:

```
[ {"type":"system","subtype":"init", ...},
  {"type":"assistant","message":{...}},
  {"type":"rate_limit_event", ...},
  {"type":"result","subtype":"success","result":"<the text>", "is_error":false,
   "total_cost_usd":0.2017, "duration_ms":4228, "num_turns":1, ...} ]
```

So:

```python
messages = json.loads(proc.stdout)
final = [m for m in messages if m.get("type") == "result"][-1]
text = final["result"]
```

Take the **last** result message and check `is_error` before using `result` — on
failure that field carries the error text, not output.

## Two things worth taking from the result message

`total_cost_usd` makes a real budget quotable instead of a session count.
Measured: **$0.20 and ~4.2s** for a single-turn proposing call.

`num_turns` distinguishes a one-shot answer from a session that went agentic.

## stdin must be redirected

Without it every invocation prints
`Warning: no stdin data received in 3s, proceeding without it` and stalls for
three seconds. Across hundreds of nested runs that is minutes of pure waiting.

```python
subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL, ...)
```

## Why this transport at all

`improve_description.py` previously used the `anthropic` SDK, needing
`ANTHROPIC_API_KEY`. A machine authenticating Claude Code through OAuth has no
key, so the optimization loop could not run at all — see
[run_loop.py needs an API key this box does not have](run-loop-needs-an-api-key-this-box-does-not-have.md).
Shelling out inherits whatever auth `claude` already has, and makes the proposing
model the same one the user runs.
