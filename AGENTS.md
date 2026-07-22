# active-skills

## Project Goal

Source of truth for a curated set of agent skills, consumed by Claude Code and Antigravity. This is the **authoring** repo — clone it to write skills.

## Project Context

**This repo is not a plugin.** It carries no manifest, no version, and no plugin machinery. Skills reach users through the `active-skills` plugin in `mlarkin00/plugins`, which mirrors this repo via `sync-active-skills.yml`.

| | Owns |
|---|---|
| **This repo** | the skills |
| `mlarkin00/plugins` → `active-skills/` | manifests, version, packaging, release |

The split exists so this stays a clean place to author. Plugin machinery living here is what made it a poor one.

Backlog for the skills themselves: `@.agents/TODO.md`. It does not sync — the mirror takes only top-level directories containing a `SKILL.md`, and `*/` does not match dot-directories.

The only thing here that reaches the plugin repo is `.github/workflows/notify-marketplace.yml`, which POSTs a `repository_dispatch` (`active-skills-updated`) to `mlarkin00/plugins` on every push to `main`. It carries no content — it is a doorbell. The secret is `MARKETPLACE_DISPATCH_TOKEN`; without it the job no-ops with a warning and the marketplace's daily 06:17 UTC poll syncs instead.

## Operational Commands

```bash
# What the sync will actually ship. A skill is a top-level directory with a
# SKILL.md; everything else at the root is skipped. Run before pushing a new skill.
for d in */; do [ -f "$d/SKILL.md" ] && echo "ship  ${d%/}" || echo "SKIP  ${d%/}"; done

# Every SKILL.md parses a name and description out of its frontmatter
for f in */SKILL.md; do
  awk -v f="$f" '/^name:/{n=1} /^description:/{d=1} END{if(!n||!d) print "INCOMPLETE frontmatter: " f}' "$f"
done
```

## Style & Conventions

- A skill is `<skill-name>/SKILL.md` at the **repo root**. Everything the skill needs (`scripts/`, `references/`, `evals/`, `assets/`) goes inside its own directory and travels with it.
- **A top-level directory without a `SKILL.md` is silently skipped by the sync** — no error, the skill just never ships. This is deliberate, so the repo can hold `docs/` or `drafts/` without them becoming phantom skills. It also means a typo'd `Skill.md` fails invisibly. The sync emits a `::notice::` listing skipped entries; that is where to look when a new skill doesn't appear.
- **Nothing here is versioned.** Do not add a manifest or a version field. The plugin's sync patch-bumps its own manifests on every mirrored change, which is why a skill edit cannot be stranded by a forgotten bump.
- Deletions propagate: the mirror is `rsync --delete`, so removing a skill here removes it from the plugin. A rename is a delete plus an add, and users lose the old name.
- There is no generated skill inventory in this README. `gen-readme.sh` lives in the plugin and regenerates the inventory there, against what actually shipped.

## Architecture & Constraints

**This repository is public.** Everything committed here, including history, is world-readable. Before adding files, check for internal paths — a pattern scan for `google3`, `go/`, and `blaze` alone is not sufficient; it missed `/google/bin/...` and internal proto paths such as `learning/gemini/...` elsewhere in this codebase.

**Do not add usage-tracking code or counts.** Tracking belongs to the separate `skill-usage` plugin. Counts are personal telemetry and must never be committed to a public repo; `skill-usage.json` and its lock/tmp siblings are gitignored as a backstop, because `SKILL_USAGE_REPO` could be pointed at a clone of this repo by accident.

**Why the SKILL.md selector matters to Antigravity.** `agy` installs *every* entry under the plugin's `skills/` directory as a skill, so a loose file mirrored in becomes a phantom skill in its UI. Selecting on `SKILL.md` is what prevents that — it is not merely tidiness.

**Never:**
- Add a `plugin.json`, `.claude-plugin/`, or any version field — this repo is not a plugin
- Add a release workflow; `mlarkin00/plugins` owns versioning and releases
- Commit usage counts
- Hand-edit anything in `mlarkin00/plugins/active-skills/skills/` — it is this repo's mirror and is overwritten on the next sync
