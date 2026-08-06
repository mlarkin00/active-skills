---
type: Pitfall
resource: skill-creator-enhanced/scripts/run_eval.py
title: Parallel trigger probes sharing one project root steal each other's command files
description: Concurrent probe runs writing into the same .claude/commands/ each see
  every other run's probe, and a session that invokes a sibling's probe carries a
  different UUID so it is scored as a miss — undercounting worse the more workers run.
tags: [evals, triggering, measurement, concurrency]
timestamp: '2026-08-06T18:15:00+00:00'
---

Probe mode measures a candidate description by writing
`<project-root>/.claude/commands/<skill>-skill-<uuid8>.md` and counting calls to
*that* name. Runs execute in parallel through a `ProcessPoolExecutor`.

With a shared project root, every concurrent run's probe file is visible to every
other run. A session picks one — often not its own. The classifier then sees a
name whose UUID does not match, and:

- `probe_name in payload` → False, so not a probe hit
- `matches_skill(fired, skill_name)` → False, so not the installed skill either

…so it lands in `OTHER` and is **scored as a miss**, even though the candidate
description is exactly what triggered. The recorded `fired` value is another
run's probe name, which is the visible symptom: a query showing `triggers=0/2`
whose `fired` list contains a probe name, and the *same* probe id appearing
across queries that ran in different processes.

Measured 2026-08-06, Claude Code 2.1.x:

```
triggers=0 runs=2 rate=0.0   fired: ['prompt-design-skill-0f27ff1a', 'prompt-design-skill-0f27ff1a']
triggers=1 runs=2 rate=0.5   fired: ['prompt-design-skill-0f27ff1a', 'prompt-design-skill-0f27ff1a']
```

One probe id across two independent queries is impossible if each run only ever
sees its own file.

## Why it matters

The bias is one-directional — it can only turn hits into misses — and it scales
with `--num-workers`. At the documented `--num-workers 10`, a session sees ten
candidate probes and has a one-in-ten chance of picking the one being counted.
Nothing in the output looks like an error; the rate is simply too low, which
reads as "this description does not trigger well".

## Fix

Each run builds its **own** project root (`tempfile.mkdtemp()` plus
`.claude/commands/`) and removes it afterwards. Claude Code treats any directory
containing `.claude/` as a project root, so the probe is still discovered.

This also fixed a second defect in the same place: probe mode previously defaulted
to the *real* repo root, where the skills exist on disk, so a session that read
`prompt-design/SKILL.md` was classified as the installed skill firing — a false
contamination signal. A scratch root has no repo files to read.

Verified after the fix: `distinct probe ids=1` per query under `--num-workers 6`,
with `contaminated_runs: 0`.
