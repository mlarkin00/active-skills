# active-skills — Claude Code

## Project rules

The repo's rules, layout, and mirror contract live in `AGENTS.md`. Read it before
changing anything under a skill directory. It is a standalone file, not a mirror of
this one — nothing here supersedes it.

## Where a finding goes

A fact that cost investigation to establish and is not derivable from the repo's
files is a **concept in `.agents/wiki/`**, version-pinned to what it was verified
against — not a `.agents/TODO.md` item. TODO holds work still to do; a closed
finding parked there sits forever looking actionable. Dev-only tooling goes in
`.agents/tools/`, which does not ship.

## Why this file exists separately

Claude Code does not read `AGENTS.md`, and `agy` does not expand `@` imports. Every
briefing file therefore needs its own copy of anything that must reach the model,
which is why the knowledge bundle appears below as an import here and as an inlined
catalog in `AGENTS.md`. Do not "consolidate" the two into a symlink — that collapses
the modes and the bundle stops reaching one of the two runtimes.

## Knowledge bundle

The block below is installed and refreshed by `llm-wiki`'s `okf_discover.py`. It is
the only thing that makes `.agents/wiki/` reachable from a Claude Code session.
Deleting it does not break anything visibly — it just silently stops the evidence
being read. Re-check with `okf_discover.py .agents/wiki --check`.

<!-- llm-wiki:discovery .agents/wiki START -->

## Knowledge bundle — `.agents/wiki`

Open the concept before re-deriving anything it covers.

@.agents/wiki/index.md

<!-- llm-wiki:discovery .agents/wiki END -->
