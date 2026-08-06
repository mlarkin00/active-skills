---
type: Pitfall
resource: skill-creator-enhanced/scripts/run_eval.py
title: run_eval.py scores every positive as a miss for a skill that is also installed
description: The probe injects a uniquely-named command file and counts only calls
  to that name, but the real installed plugin skill wins the call, so trigger rates
  read 0.00 for descriptions that are in fact firing correctly.
tags: [evals, skill-creator-enhanced, triggering, measurement]
timestamp: '2026-08-06T02:50:00+00:00'
---

`run_eval.py` measures triggering by writing a throwaway command file at
`.claude/commands/<skill>-skill-<uuid8>.md` carrying the description under test,
then running `claude -p <query>` and watching the stream for a `Skill` tool call
whose input contains that unique name. Anything else — including a `Skill` call to
a *different* skill — is scored as "did not trigger".

Every skill in this repo is also published through the `mlarkin00-plugins`
marketplace and installed at the user level, so a nested `claude -p` sees both the
probe copy and the real one. The real one wins, and the probe never fires.

Measured 2026-08-06 against `prompt-design`, Claude Code 2.1.x:

```
$ python3 -m scripts.run_eval --eval-set smoke.json --skill-path ../prompt-design \
    --runs-per-query 1
  "query": "Write me a prompt I can paste into Gemini that summarizes our sprint retro."
  "should_trigger": true,  "trigger_rate": 0.0,  "pass": false
```

The same query, run directly with the probe command file present, shows what
actually happened:

```
TOOL_USE: Skill {"skill": "active-skills:prompt-design", "args": "..."}
```

The description triggered. `run_eval.py` reported a miss.

## Why it matters

The failure is silent and reads as a real result: a table of `trigger_rate: 0.00`
against `should_trigger: true` looks exactly like a description that nobody
matches. Acting on it means rewriting a description that was already working — and
because the rewrite still scores 0.00, the loop never converges. `run_loop.py`
inherits this, so an unattended optimization run would iterate a description
towards nothing.

The negatives are unaffected (they score 0.00 and pass), so a run can look
half-plausible rather than obviously broken.

## What to do instead

Measure against the **live** skill set and record which skill actually fired, which
is also the measurement the competing-descriptions question needs — `prompt-design`,
`new-prompt`, and `optimizing-prompts-w-vertex` overlap, and only a run where all
three are present shows which one wins a near-miss query. Parse the same stream
events `run_eval.py` does, but accept any `Skill` call and compare its `skill`
argument against the plugin-qualified name (`active-skills:prompt-design`).

`.agents/tools/trigger_eval.py` does this. It lives under `.agents/` deliberately:
that path is outside the plugin mirror, which takes only top-level directories
containing a `SKILL.md`, so a dev-only runner there does not ship to users. Fold it
into `run_eval.py` when that is fixed, rather than leaving two runners.

```bash
python3 .agents/tools/trigger_eval.py \
  --eval-set <skill>/evals/trigger_optimization/eval_set.json \
  --skill <skill-name> --cwd <empty-scratch-dir> \
  --runs-per-query 3 --num-workers 10 --out results.json
```

Run it from a scratch directory with no project files: the query is answered by a
real nested session, and a repo full of source will send it reading code instead of
choosing a skill. A query that cannot be answered without an artifact the session
cannot see (\"tighten up our bot's system prompt\", with no prompt pasted) makes the
model go looking for the file and ask for it — correct behaviour, but it scores as
a non-trigger and tests nothing. Keep eval queries self-contained.

Uninstalling the plugin to unblock `run_eval.py` also works and is worse: it
removes the competitors along with the duplicate, so near-miss queries stop being
discriminating.

See [run_loop.py cannot run on this box](run-loop-needs-an-api-key-this-box-does-not-have.md)
for the second reason the documented loop does not run here, and
[3 runs per query cannot separate two descriptions](three-runs-per-query-cannot-separate-two-descriptions.md)
for why fixing the detection still does not make the default sample size conclusive.
