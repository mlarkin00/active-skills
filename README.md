# active-skills

The source of truth for a curated set of agent skills, used by Claude Code and Antigravity.

**This repository holds skills and nothing else.** It is not a plugin and is not installed directly. Skills reach users through the `active-skills` plugin in [`mlarkin00/plugins`](https://github.com/mlarkin00/plugins), which mirrors this repo automatically.

Clone this repo to *write* skills. Install the plugin to *use* them.

## How a skill gets from here to users

```
edit a skill → push to main
    → notify-marketplace.yml pings mlarkin00/plugins
    → sync-active-skills.yml mirrors the skills into the plugin,
      bumps its version, tags, and releases
    → the next marketplace update delivers it
```

There is nothing to bump and nothing to release here. The plugin owns its own version and the sync bumps it on every change, so a skill edit cannot get stranded by a forgotten version bump.

If the dispatch fails or the token is missing, a daily poll at 06:17 UTC picks the change up instead. Nothing is lost; it just arrives later.

## Authoring

**A skill is a top-level directory containing a `SKILL.md`.** That is the entire contract, and it is exactly what the sync selects on.

```
systematic-debugging/
├── SKILL.md              ← required; this is what makes it a skill
├── references/
└── scripts/
```

Anything inside a skill directory travels with it — `scripts/`, `references/`, `evals/`, `assets/`, whatever the skill needs.

Anything at the repo root that is **not** a directory with a `SKILL.md` is skipped by the sync. So `README.md`, `.github/`, and any future `docs/` or `drafts/` stay here and never ship. You can add non-skill content freely.

> **The one trap:** a directory with a missing or misspelled `SKILL.md` is silently skipped, not flagged — the skill simply never appears for users. The sync logs what it skipped as a notice on its run, which is where to look when a new skill doesn't show up.

Check what will ship before you push:

```bash
for d in */; do [ -f "$d/SKILL.md" ] && echo "ship  ${d%/}" || echo "SKIP  ${d%/}"; done
```

Deletions propagate too — the mirror uses `--delete`, so removing a skill here removes it from the plugin. A rename is a delete plus an add.

## Publishing

Push to `main`. That's all.

## Installing

Install the plugin, not this repo.

**Claude Code:**

```
/plugin marketplace add mlarkin00/plugins
/plugin install active-skills@mlarkin00-plugins
```

Skills are namespaced under the plugin, e.g. `active-skills:systematic-debugging`.

**Antigravity** — clone the marketplace repo once, then bulk-install from it:

```bash
git clone https://github.com/mlarkin00/plugins
agy plugin install ./plugins
```

Pointing `agy plugin install` at a directory holding several plugins reports `Found bulk plugins directory` and installs them all, this one included.

## A note on the old layout

Skills used to live under a `skills/` subdirectory here, and this repo used to be a plugin itself, carrying both runtimes' manifests. Both are gone — skills sit at the root, and all plugin machinery lives in `mlarkin00/plugins`. If you have a local tool or symlink pointing at `active-skills/skills/`, repoint it at the repo root.
