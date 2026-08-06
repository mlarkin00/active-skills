---
type: Runtime Behaviour
resource: skill-creator-enhanced/scripts/run_eval.py
title: Passing enabledPlugins via --settings hides a plugin from one claude -p run
description: A JSON string given to --settings merges over the user's settings for
  that process only, so setting enabledPlugins.<plugin@marketplace> to false removes
  the plugin's skills from a nested run without touching the user's environment.
tags: [evals, triggering, claude-cli, isolation]
timestamp: '2026-08-06T18:00:00+00:00'
---

Measuring whether a *candidate* skill description triggers requires the real
skill to be absent — otherwise the installed copy carries the shipped description
and wins the call. The obvious lever, `claude plugin disable <plugin>`, is global:
it changes the user's interactive sessions, persists until undone, and has to be
remembered.

`--settings` takes a JSON **string** as well as a path, and it merges over the
user's settings for that process alone. `enabledPlugins` is a real settings key,
shaped `{"<plugin>@<marketplace>": true|false}`.

```bash
claude -p "<query>" --output-format json \
  --settings '{"enabledPlugins":{"active-skills@mlarkin00-plugins":false}}'
```

Verified 2026-08-06, Claude Code 2.1.x. A query that fires
`active-skills:prompt-design` on a bare run fires nothing with the override, and
the `system/init` message's skill list drops from 60-plus entries to **zero**
`active-skills` entries.

## Deriving the key

The settings key is `<plugin>@<marketplace>`, recoverable from the install path:

```
~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/skills/<name>/SKILL.md
~/.claude/plugins/marketplaces/<marketplace>/<plugin>/skills/<name>/SKILL.md
```

`run_eval.isolation_settings()` builds the JSON from that; `find_installed()`
does the lookup.

## Limits

The unit is the **plugin**, not the skill, so every sibling skill in the same
plugin disappears with it. For measuring positives that is fine. For measuring
over-triggering against those siblings it destroys the thing being measured —
use live mode there.

A copy installed at `~/.claude/skills/<name>/` is not a plugin and cannot be
disabled this way; it has to be moved aside.

## What does NOT work

A subagent cannot do this. Agent frontmatter is `name`, `description`, `tools`,
`model`, `color` — there is no skills-scoping field, and the only lever, `tools`,
would have to drop `Skill` itself, which makes trigger measurement impossible by
construction.

`claude --bare` skips plugin sync but requires `ANTHROPIC_API_KEY`, which an
OAuth-authenticated machine does not have. `--disable-slash-commands` removes
every skill, not one.

See [a trigger probe scores an installed skill as a miss](run-eval-scores-an-installed-skill-as-a-miss.md)
for why the isolation is needed at all.
