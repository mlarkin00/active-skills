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

Backlog for the skills themselves: `.agents/TODO.md`. It does not sync — the mirror takes only top-level directories containing a `SKILL.md`, and `*/` does not match dot-directories.

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
- Deletions propagate: the mirror is `rsync --delete`, so removing a skill here removes it from the plugin. A rename is a delete plus an add, and users lose the old name. After removing a skill, sweep the surviving ones for its name — and repair only the pointers, never the citations, per `.agents/wiki/publishing/removing-a-skill-leaves-two-kinds-of-reference.md`.
- There is no generated skill inventory in this README. `gen-readme.sh` lives in the plugin and regenerates the inventory there, against what actually shipped.
- **Dev-only tooling goes in `.agents/tools/`, never inside a skill directory.** A skill's own subdirectories ship to users; `.agents/` does not, because the sync globs `*/` and that does not match dot-directories. Anything that exists to develop or measure the skills rather than to run them belongs there. Note the directory is currently absent — it is created on demand, not a fixture.

## Architecture & Constraints

**This repository is public.** Everything committed here, including history, is world-readable. Before adding files, check for internal paths — a pattern scan for `google3`, `go/`, and `blaze` alone is not sufficient; it missed `/google/bin/...` and internal proto paths such as `learning/gemini/...` elsewhere in this codebase. A path scan also cannot catch internal **service codenames** written as fluent prose — a research doc dropped here named six unreleased services as if they were shipping products. Verify product names against public docs before committing a research doc or anything distilled from one: `.agents/wiki/publishing/research-docs-carry-internal-codenames-a-path-scan-misses.md`.

**Do not add usage-tracking code.** Tracking belongs to the separate `skill-usage` plugin. The *counts* it writes are a different matter and the distinction is load-bearing: the per-machine shards under `skill-usage/` **are** tracked here by deliberate choice, sharded so several machines never conflict, and they commit as their own `chore(active-skills): update skill usage counts`. Pointing `SKILL_USAGE_REPO` at this repo is the intended setup, not an accident — it is why those shards exist. What is banned is the **root-level** `skill-usage.json` and `.skill-usage.lock`, the pre-sharding layout. Only plugin versions predating the per-machine split write them; current ones shard and keep the lock in `~/.cache/skill-usage/locks/`, deliberately outside the repo. So a root file appearing is a stale *version* artifact, not a misconfiguration and not corruption — `report-usage.py` still sums it and labels it `(pre-sharding)`. Both are gitignored with a leading `/` so the shards still commit and an older version elsewhere cannot resurrect the old layout here. `.gitignore` is the authority; read it before "fixing" a counts file.

**Why the SKILL.md selector matters to Antigravity.** `agy` installs *every* entry under the plugin's `skills/` directory as a skill, so a loose file mirrored in becomes a phantom skill in its UI. Selecting on `SKILL.md` is what prevents that — it is not merely tidiness.

**`AGENTS.md` and `CLAUDE.md` reach different runtimes and are not redundant.** Claude Code reads `CLAUDE.md` and never `AGENTS.md`; `agy` reads `AGENTS.md` and never expands `@` imports. That is why the bundle appears below as an inlined catalog and in `CLAUDE.md` as a one-line import — each runtime gets exactly one copy. Deleting or symlinking either file collapses the arrangement and silently cuts a runtime off from the bundle.

**Findings go in `.agents/wiki/`, not `.agents/TODO.md`.** A fact that cost investigation to establish and is not derivable from these files is a concept in the bundle, version-pinned. TODO holds work still to do. A closed finding parked in TODO sits there forever looking actionable.

**Design docs go in `docs/designs/YYYY-MM-DD-<slug>.md`.** `docs/` has no `SKILL.md`, so the sync skips it. Do not put a design doc inside a skill directory (it would ship to users) and do not name one `DESIGN.md` at the repo root — that filename is reserved for a design-system spec in the `google/design.md` format.

**Never:**
- Add a `plugin.json`, `.claude-plugin/`, or any version field — this repo is not a plugin
- Add a release workflow; `mlarkin00/plugins` owns versioning and releases
- Commit a root-level `skill-usage.json` or `.skill-usage.lock` (the sharded files under `skill-usage/` are fine — see above)
- Hand-edit anything in `mlarkin00/plugins/active-skills/skills/` — it is this repo's mirror and is overwritten on the next sync
- Symlink `AGENTS.md` and `CLAUDE.md` together, or drop one as duplicative

<!-- llm-wiki:discovery .agents/wiki START -->

## Knowledge bundle — `.agents/wiki`

Open the concept before re-deriving anything it covers.

### Subdirectories

* [evals](.agents/wiki/evals/index.md) - Contains 8 entries: claude -p --output-format json returns an array of messages, not a result object, Killing an eval runner leaves its nested claude -p sessions running and billing, OpenCode sessions store no queryable injected-context epoch, unlike Claude Code's attachment records, Parallel trigger probes sharing one project root steal each other's command files, A trigger probe scores every positive as a miss for a skill that is also installed, An SDK-based propose step cannot run on an OAuth-authenticated machine, Passing enabledPlugins via --settings hides a plugin from one claude -p run, Trigger evals at 3 runs per query cannot separate two skill descriptions.
* [publishing](.agents/wiki/publishing/index.md) - Contains 3 entries: Editing a skill in this repo does not change what its slash command runs, Removing a skill leaves two kinds of reference, and only one of them may be edited, Deep-research source docs name internal services in prose that no path scan catches.

<!-- llm-wiki:discovery .agents/wiki END -->
