---
type: Runtime Behaviour
resource: show-context/scripts/show_context.py
title: OpenCode sessions store no queryable injected-context epoch, unlike Claude Code's attachment records
description: OpenCode persists the conversation (message/part tables) but not a
  session_context_epoch — that table is empty across every session in the DB, so a
  show-context-style reader cannot enumerate injected instruction files, hooks,
  or skill/MCP listings from ground truth the way the Claude Code backend can.
tags: [opencode, session-transcript, show-context, harness-agnostic, sqlite]
timestamp: '2026-08-19T22:32:00+00:00'
---

OpenCode stores sessions in a SQLite DB at
`~/.local/share/opencode/opencode.db`, not a JSONL transcript. When the
`show-context` skill was made harness-agnostic (2026-08-19), the OpenCode path
needed a ground-truth reader equivalent to Claude Code's `attachment` records.
It does not have one.

Measured 2026-08-19 against OpenCode (the running harness on this machine,
`$OPENCODE=1`), session `ses_fe3ead2c7ffehTNd6vyRcYZ167`:

```
session_context_epoch rows (whole DB, 83 sessions):  0
session_input rows (this session):                    0
session_message rows (this session):                  0
message rows (this session):                         39
part rows (this session):                           179
  tool: 42 · text: 34 · step-start: 34 · step-finish: 33 · reasoning: 30 · patch: 11
event rows (whole DB):                          26,513  (keyed by aggregate_id)
```

So `session_context_epoch` — the table that *should* hold the baseline + snapshot
of injected context per session — is empty for the in-flight session **and for
every other session in the DB**. This is not the "in-flight turn may not be
flushed yet" caveat from `show-context/SKILL.md`; it is never written here at
all. The conversation itself *is* recorded (in `message` + `part`), and
injected **prompt content** (slash-command bodies, skill bodies) appears as
`text` parts — the OpenCode analogue of Claude Code's `meta` section. But the
typed manifest of *what was injected* (instruction files with scope and
staleness, hook outputs, skill/agent/tool/MCP listings, permissions) has no
persisted record a reader can enumerate.

## What this means for a harness-agnostic show-context

The skill's principle — read ground truth, never introspect — still holds, but
its *coverage* differs by harness:

| Harness | Conversation | Injected-context manifest |
|---|---|---|
| Claude Code | JSONL `user`/`assistant` records | `attachment` records (typed, queryable) |
| OpenCode | `message` + `part` tables | **not persisted** — only prompt-content `text` parts survive |

So in OpenCode the skill can confirm a session ran and render its conversation,
but it **cannot** faithfully answer "did my AGENTS.md load?" or "which hooks
injected what?" from ground truth. Saying so plainly is the correct behaviour,
not a gap to paper over with introspection. The bundled `show_context.py`
handles this by detecting OpenCode and printing a pointer to the native
`session_*` tools rather than trying to parse a foreign format.

## A secondary wrinkle

The native `session_list` tool returned "No sessions found" despite the DB
holding 83 sessions including the current one. The DB is the ground truth; the
tool-wrapper discrepancy is reported as a fact, not diagnosed here.
