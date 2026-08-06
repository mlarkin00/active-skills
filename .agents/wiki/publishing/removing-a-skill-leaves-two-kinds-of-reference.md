---
type: Convention
resource: .agents/wiki/publishing
title: Removing a skill leaves two kinds of reference, and only one of them may be edited
description: A pointer that tells a future agent to go somewhere must be repaired;
  a citation recording what was observed must not, because rewriting it falsifies
  the measurement. Re-pin the prose that frames the citation instead.
tags: [publishing, skill-removal, evals, provenance]
timestamp: '2026-08-06T20:35:00+00:00'
---

Deleting a skill from this repo strands every mention of its name. Those mentions
are not one category, and treating them as one destroys evidence.

**Pointers — repair them.** Text that directs a future agent somewhere. A dangling
pointer sends the agent to a directory that is not there, and nothing reports it:

| Where they hide | Example found 2026-08-06 |
| :--- | :--- |
| `## Integration` sections | `close-session/SKILL.md` named three deleted skills, including a 3-bullet comparison against one |
| eval prompts | `skill-improvement/evals/evals.json` asked the agent to audit `active-skills/refresh-skills` |
| doc examples | `README.md` used `systematic-debugging/` as the layout example and the namespacing example |
| naming examples | `skill-creator-enhanced/SKILL.md` used `code-design` to illustrate kebab-case |

**Citations — leave them.** Text recording what was *observed*, at a time when the
skill existed. `prompt-design/evals/trigger_optimization/eval_results_1.json`
carries `"fired": ["active-skills:optimizing-prompts-w-vertex"]`. That is the
measurement as taken. Editing it to name a surviving skill would assert a run that
never happened. Concepts in this bundle are the same: they are version-pinned
evidence, and the name of a since-removed competitor is part of the evidence.

**The prose framing a citation is a third thing, and it does rot.** The eval README
claimed the negatives "include the in-repo skills that compete on overlapping
phrasing" and that "the Vertex and Cloud Build queries route to the right skills."
Both were true when measured and false the moment the competitor was deleted. The
fix is to re-pin, not to rewrite: state that the runs predate the removal and say
what the affected query now tests. See that README's "Query 11 lost its owner"
note, added the same day.

## Finding them

The sweep that produced the table above, run from the repo root with `$REMOVED` as
an alternation of the deleted skill names:

```bash
grep -rnEI "$REMOVED" --exclude-dir=.git . \
  | grep -vE '^\./(skill-usage/|\.agents/wiki/)' \
  | grep -vE 'eval_results_[0-9]'
```

The two exclusions are the citation classes. Everything that survives the filter is
a pointer and should be read as a defect until shown otherwise — with one trap:
substring collisions. `handoff` matches "design-handoff" in an unrelated eval query,
so confirm each hit before editing.

Sibling check, because a removal can also strand a path rather than a name: verify
every `references/`, `scripts/`, and `assets/` reference inside each surviving skill
still resolves. Most apparent misses are false positives — they point at another
plugin's scripts or at the skill *being* audited, not at anything in this repo.
