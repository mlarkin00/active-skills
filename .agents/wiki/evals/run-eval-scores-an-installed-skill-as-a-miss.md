---
type: Pitfall
resource: skill-creator-enhanced/scripts/run_eval.py
title: A trigger probe scores every positive as a miss for a skill that is also installed
description: Injecting a uniquely-named command file and counting only calls to that
  name reads 0.00 for descriptions that are in fact firing, because the installed
  plugin skill wins the call; fixed 2026-08-06 by adding a live mode and by counting
  contaminated runs as unmeasured rather than failed.
tags: [evals, skill-creator-enhanced, triggering, measurement]
timestamp: '2026-08-06T02:50:00+00:00'
---

> **Fixed 2026-08-06.** `run_eval.py` now has `--mode live` (measures the installed
> skill, default when no `--description` is given) and probe mode reports runs the
> installed skill won as `unmeasured`, not failed. The account below is why the
> modes exist; do not collapse them back into one.

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

## The fix, as shipped

`run_eval.py` accepts any `Skill` call and compares its `skill` argument against
the skill under test, matching bare (`prompt-design`) or plugin-qualified
(`active-skills:prompt-design`) — suffix match on `:<name>`, never substring, since
`prompt-design` is a substring of `prompt-design-v2`. It records the name that
fired, per run, which is the measurement the competing-descriptions question needs:
`prompt-design`, `new-prompt`, and `optimizing-prompts-w-vertex` overlap, and only
a run where all three are present shows which wins a near-miss query.

Two modes, because they answer different questions:

| Mode | Measures | Trigger is |
| :--- | :--- | :--- |
| `live` (default) | the **shipped** description, against real competitors | a call to the skill under test |
| `probe` (implied by `--description`) | a **candidate** description not installed anywhere | a call to the throwaway probe name |

```bash
cd skill-creator-enhanced
python3 -m scripts.run_eval \
  --eval-set ../<skill>/evals/trigger_optimization/eval_set.json \
  --skill-path ../<skill> \
  --mode live --cwd "$(mktemp -d)" \
  --runs-per-query 10 --num-workers 10 --timeout 120 > results.json
```

Verified 2026-08-06, Claude Code 2.1.x: the `prompt-design` positive that read
`trigger_rate: 0.0` above now reads `1.0` with `fired: ["active-skills:prompt-design"]`,
and the Vertex negative passes showing `fired: ["active-skills:optimizing-prompts-w-vertex"]`.

Probe mode cannot be de-contaminated in this environment — Claude Code loads
user-level plugins regardless of cwd, and the only flags that would strip them
(`--bare`, `--disable-slash-commands`) either need an API key this box does not have
or remove every skill. So probe mode **counts** the runs the installed skill won and
excludes them: they appear as `contaminated`, a fully-contaminated query reports
`pass: null` / `UNMEAS` rather than a failure, and `run_loop.py` aborts outright
above 25% contamination rather than iterating a working description toward nothing.

Run from a scratch directory with no project files. A query that cannot be answered
without an artifact the session cannot see ("tighten up our bot's system prompt",
with no prompt pasted) makes the model go looking for the file and ask for it —
correct behaviour, but it scores as a non-trigger and tests nothing. Keep eval
queries self-contained.

Uninstalling the plugin to unblock probe mode works and is worse: it removes the
competitors along with the duplicate, so near-miss queries stop being
discriminating. Prefer live mode.

See [run_loop.py cannot run on this box](run-loop-needs-an-api-key-this-box-does-not-have.md)
for the second reason the documented loop does not run here, and
[3 runs per query cannot separate two descriptions](three-runs-per-query-cannot-separate-two-descriptions.md)
for why fixing the detection still does not make the default sample size conclusive.
