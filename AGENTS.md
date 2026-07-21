# active-skills

## Project Goal

Source of truth for a curated set of agent skills and their usage tracking, consumed by both Claude Code and Antigravity. Marketplaces reference this repository directly; nothing here is a vendored copy of anything else.

## Project Context

The repository root **is** the plugin. Two manifests coexist because the runtimes read different paths:

| Runtime | Manifest | Version |
|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `0.2.1` |
| Antigravity | `plugin.json` | `0.1.11` |

Versions are deliberately independent — a Claude-only hook fix must not force an empty Antigravity release. Each runtime ignores the other's files.

Pure Python for deterministic work, no build step, no Node.

## Operational Commands

```bash
# Regenerate the README skill inventory (run after adding/removing/retitling a skill)
bash scripts/gen-readme.sh

# Antigravity sidecar tests (unittest — pytest is not a dependency)
python3 -m unittest discover -s tests -q

# Validate every manifest parses
python3 -c "import json;[json.load(open(f)) and print('OK',f) for f in ['.claude-plugin/plugin.json','plugin.json','hooks/hooks.json','sidecars/check-updates/sidecar.json']]"

# Exercise the tracker against a synthetic hook payload
CLAUDE_PLUGIN_ROOT=$PWD ACTIVE_SKILLS_USAGE_REPO=/tmp/t \
  sh -c 'echo "{\"tool_name\":\"Skill\",\"tool_input\":{\"skill\":\"gcloud\"}}" | python3 scripts/track-usage.py'
```

## Style & Conventions

- Each skill MUST live in `skills/<skill-name>/` with a `SKILL.md`. Skill membership is a **directory** test, so a loose file under `skills/` is never counted as a skill.
- Keep `scripts/usage_lib.py` runtime-neutral. Anything that parses a Claude Code hook payload belongs in `track-usage.py` / `sync-usage.py`, so a second runtime can reuse the core without a fork.
- Bump the manifest a change actually affects. A skill edit affects both; a `hooks/` edit affects only Claude.
- Run `gen-readme.sh` after any skill change — the block between `<!-- SKILLS:START -->` and `<!-- SKILLS:END -->` is generated and MUST NOT be hand-edited.

## Architecture & Constraints

**This repository is public.** Everything committed here, including history, is world-readable.

**Usage counts are private and MUST NOT be committed here.** The tracker writes to whatever `ACTIVE_SKILLS_USAGE_REPO` names — point it at a *private* repo. `skill-usage.json` is gitignored as a backstop, but the gitignore is the second line of defence, not the first.

**Hooks MUST exit 0 on every path.** Malformed stdin, missing repo, non-git directory, failed push — a tracker that blocks a session is worse than one that misses a count.

**Concurrency.** Counts are written under an exclusive `flock` with atomic tmp+rename, because parallel sessions increment the same file. Do not replace this with a plain read-modify-write.

**Never:**
- Commit usage counts, or point `ACTIVE_SKILLS_USAGE_REPO` at this repo
- Hand-edit the generated skill inventory in `README.md`
- Add runtime-specific branching to `usage_lib.py`
- Assume a marketplace holds a copy to fall back on — there is none, by design
