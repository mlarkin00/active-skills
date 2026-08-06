---
type: Pitfall
resource: skill-creator-enhanced/scripts/run_loop.py
title: An SDK-based propose step cannot run on an OAuth-authenticated machine
description: Calling the Anthropic API directly needs ANTHROPIC_API_KEY, which a
  machine authenticating Claude Code through OAuth does not have; resolved
  2026-08-06 by shelling out to claude -p, the same transport the eval half uses.
tags: [evals, skill-creator-enhanced, environment]
timestamp: '2026-08-06T02:50:00+00:00'
---

> **Resolved 2026-08-06.** `improve_description.py` now delegates to
> `scripts/propose.py`, which shells out to `claude -p` and inherits the user's
> auth; no script in the skill imports `anthropic` any more. The account below is
> why the transport is what it is — do not "simplify" it back to the SDK, which
> would break the loop for every OAuth user, not just this box. Call shape in
> [claude -p --output-format json returns an array](claude-p-json-output-is-an-array.md).

`run_loop.py` is documented as the entry point for description optimization, but it
is two halves with different requirements:

- `run_eval.py` shells out to `claude -p` as a subprocess — no API key, works here.
- `improve_description.py` constructs `anthropic.Anthropic()` and calls the API
  directly — needs the `anthropic` package and `ANTHROPIC_API_KEY`.

`run_loop.py` imports both at module scope, so it fails before the first eval runs.
Checked 2026-08-06:

```
$ python3 -c "import anthropic"
ModuleNotFoundError: No module named 'anthropic'
$ echo "${ANTHROPIC_API_KEY:+set}"      # -> empty
```

Installing the SDK does not fix it. This box authenticates Claude Code through
OAuth, not an API key, and there is no key to fall back on.

## Why it matters

`.agents/TODO.md` items that say "use `run_loop.py`" are not executable as written.
The loop is the part that proposes the next candidate description; without it the
propose step is manual, which changes the shape of the task from "launch and wait"
to "measure, edit, re-measure" — worth knowing before planning around it.

## What to do instead

Run `run_eval.py` directly — but note it does not measure what it claims to here;
see [run_eval.py scores an installed skill as a miss](run-eval-scores-an-installed-skill-as-a-miss.md)
for why, and for the live-skill-set runner to use instead. Read the failures, edit
the description by hand, and re-measure. The train/test holdout `run_loop.py`
provides is lost, so guard against overfitting by keeping the near-miss negatives
fixed and not tuning wording against a single failing query.
