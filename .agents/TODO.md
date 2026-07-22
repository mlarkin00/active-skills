# TODO

Backlog for the skills themselves. Not synced to the plugin — the mirror only
takes top-level directories containing a `SKILL.md`, and the `*/` glob does not
match dot-directories.

## P1 — Important / Unblocking

_(none)_

## P2 — Nice-to-Have

- [ ] **[P2]** Run description optimization for `prompt-design`. The TCREI rewrite (2026-07-22) shipped with a hand-written description that was never tested for triggering. It matters more than usual here because three skills now compete on overlapping phrasing — `prompt-design`, `new-prompt`, and `optimizing-prompts-w-vertex` — and the near-miss cases are what separate them. Use `skill-creator-enhanced`'s `scripts/run_loop.py` against ~20 realistic queries.

- [ ] **[P2]** Sharpen or drop one assertion in `prompt-design/evals/evals.json`. Grading the TCREI rewrite showed eval-1 assertion 5 ("does not fabricate an audience or format") passes for any response that asks questions at all, so it discriminates nothing. Worth fixing before the eval set is expanded, since a non-discriminating assertion inflates future pass rates.

- [ ] **[P2]** Reconcile the `@`-import model with `llm-wiki`'s own discoverability P1, which proposes a `SessionStart` hook injecting the root index. The import supersedes the hook for any host that supports briefing-file imports (Claude Code, Gemini CLI), so the hook should be documented there as the **fallback for hosts without them**, not the primary mechanism — and `/llm-wiki:init` should offer to write the import line into the host repo's briefing file. Filed against `llm-wiki` in `mlarkin00/plugins`; this is the skills-side half, and the skills-side model has now landed (`managing-agent-instructions` Phase 6 + `references/knowledge-bundle.md`).

- [ ] **[P2]** Consider scaffolding `.agents/wiki/` for this repo itself. `managing-agent-instructions` Phase 6 now mandates a bundle in every project, and this repo has none — the skills prescribe a discipline they don't yet practise. Only worth doing if there are findings that pass the scope test (cost investigation, not derivable from the skill files); the option-(b) dependency decision is already recorded in the skill text itself, so it does not need a concept.
