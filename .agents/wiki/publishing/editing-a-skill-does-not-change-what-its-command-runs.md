---
type: Pitfall
resource: .agents/wiki/publishing
title: Editing a skill in this repo does not change what its slash command runs
description: The runtime loads skills from a versioned plugin cache, never from this
  authoring repo, so invoking a skill you just edited silently executes the pre-edit
  text — confirmed by running /close-session against an edited close-session and
  getting the old workflow back.
tags: [publishing, plugin-cache, skill-authoring, sync]
timestamp: '2026-08-07T18:35:00+00:00'
---

Editing `<skill>/SKILL.md` here changes the **source**. It does not change what
`/<skill>` executes in this or any concurrent session. The runtime loads from a
versioned copy under the plugin cache:

```
~/.claude/plugins/cache/mlarkin00-plugins/active-skills/<version>/skills/<skill>/SKILL.md
```

Observed 2026-08-07, Claude Code 2.1.x, active-skills 0.2.21. `close-session/SKILL.md`
had just been rewritten — description replaced, `category: git` corrected to
`metadata: category: team-automation`, a triage step added ahead of the documentation
pass. Invoking `/close-session` immediately after loaded the **pre-edit** body: old
description, `category: git`, and the original step order with the expensive
`managing-agent-instructions` call still in position one.

```bash
diff -q close-session/SKILL.md \
  ~/.claude/plugins/cache/mlarkin00-plugins/active-skills/0.2.21/skills/close-session/SKILL.md
# → differ
```

## Why nothing warns you

The full chain from an edit here to a refreshed cache is: commit → push to `main` →
`repository_dispatch` doorbell (or the 06:17 UTC poll) → `sync-active-skills.yml`
mirrors into `mlarkin00/plugins` → that repo patch-bumps its manifests → the local
plugin installs the new version. Every leg is asynchronous and none of them reports
back into the session that made the edit. The skill simply loads and runs, looking
entirely normal.

The cache keeps every version it has installed — 0.2.7 and 0.2.17 through 0.2.21 were
all present on this machine — so a stale copy is never missing, just old. What
refreshes the local cache, and whether it needs an explicit plugin update, was not
established here.

The trap has a second half. When a skill loads, the base directory reported to the
agent is the **cache path**, not the repo path. An agent that follows the skill's own
instructions to open `scripts/` or `references/` reads the cached copies too, so an
edit to a bundled resource is invisible in exactly the same way, with no frontmatter
difference to make it noticeable.

## What to do instead

Verify a skill edit by reading the file you edited. Do not verify it by invoking the
skill — that measures the last published version, which is the one thing the edit did
not touch.

To see what is actually live, diff the two paths as above. A tidier check across the
whole repo, since the cache mirrors this repo's top-level skill directories one for one:

```bash
CACHE=~/.claude/plugins/cache/mlarkin00-plugins/active-skills/<version>/skills
for d in */; do
  [ -f "$d/SKILL.md" ] || continue
  diff -q "$d/SKILL.md" "$CACHE/${d%/}/SKILL.md" >/dev/null 2>&1 \
    || echo "unpublished: ${d%/}"
done
```

The corollary for this bundle's own subject matter: a trigger eval run from a working
copy measures the **published** description, not the candidate in the tree. That is a
separate failure from the probe-isolation ones in
[../evals/settings-json-isolates-a-plugin-per-invocation.md](../evals/settings-json-isolates-a-plugin-per-invocation.md),
and it biases toward a false negative — the candidate never ran.
