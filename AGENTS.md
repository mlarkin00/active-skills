# active-skills

## Project Goal

Source of truth for a curated set of agent skills and their usage tracking, consumed by both Claude Code and Antigravity. Marketplaces reference this repository directly; nothing here is a vendored copy of anything else.

## Project Context

The repository root **is** the plugin. Two manifests coexist because the runtimes read different paths:

| Runtime | Manifest | Hooks | Version |
|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `hooks/hooks.json` | `0.2.1` |
| Antigravity | `plugin.json` | `hooks.json` | `0.1.11` |

Claude nests, Antigravity does not — so both runtimes' files coexist and each is invisible to the other. Verified: `agy plugin validate` reports `hooks: skipped (not found)` when only `hooks/hooks.json` is present.

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

- Each skill MUST live in `skills/<skill-name>/` with a `SKILL.md`, and `skills/` MUST contain **nothing but skill directories**. Antigravity installs every entry there as a skill — a loose file becomes a phantom skill in its UI. The eval suite lives in `evals/` for exactly this reason.
- Keep `scripts/usage_lib.py` and `scripts/sync-usage.py` runtime-neutral. Payload parsing belongs in the per-runtime adapters — `track-usage.py` (Claude) and `track-usage-agy.py` (Antigravity) — so neither runtime forks the core.
- Membership MUST stay a directory test against this plugin's own `skills/`. Never introduce a hand-maintained list of skill names; it would have to be updated on every skill change and would drift silently.
- Bump the manifest a change actually affects. A skill edit affects both; a `hooks/` edit affects only Claude.
- Run `gen-readme.sh` after any skill change — the block between `<!-- SKILLS:START -->` and `<!-- SKILLS:END -->` is generated and MUST NOT be hand-edited.

## Architecture & Constraints

**This repository is public.** Everything committed here, including history, is world-readable.

**Usage counts are private and MUST NOT be committed here.** The tracker writes to whatever `ACTIVE_SKILLS_USAGE_REPO` names — point it at a *private* repo. `skill-usage.json` is gitignored as a backstop, but the gitignore is the second line of defence, not the first.

**Hooks MUST exit 0 on every path.** Malformed stdin, missing repo, non-git directory, failed push — a tracker that blocks a session is worse than one that misses a count.

**Antigravity `hooks.json` MUST contain only `PostToolUse`.** Adding a `Stop` block silently stops `PostToolUse` from firing — the plugin still installs, `agy` still reports the hooks as processed, and nothing errors; counts simply never appear. Verified against `agy` 1.1.5: a separate named hook block does not avoid it. Only `PostToolUse` fires in `--print` mode at all; `PreInvocation`, `PostInvocation`, and `Stop` never fired in testing. This is why the Antigravity flush is a scheduled sidecar rather than a lifecycle hook.

`PostToolUse` handlers MUST use the nested `{"matcher": ..., "hooks": [...]}` form. The flat `{"type": "command", ...}` form parses and installs but never fires — note that `agy-plugins/agent-memory` and `memory-bank` both use the flat form, so their hooks are likely dead.

**Concurrency.** Counts are written under an exclusive `flock` with atomic tmp+rename, because parallel sessions increment the same file. Do not replace this with a plain read-modify-write.

**Never:**
- Commit usage counts, or point `ACTIVE_SKILLS_USAGE_REPO` at this repo
- Hand-edit the generated skill inventory in `README.md`
- Add runtime-specific branching to `usage_lib.py`
- Assume a marketplace holds a copy to fall back on — there is none, by design
