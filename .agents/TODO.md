# TODO

Backlog for the skills themselves. Not synced to the plugin — the mirror only
takes top-level directories containing a `SKILL.md`, and the `*/` glob does not
match dot-directories.

## P1 — Important / Unblocking

- [ ] **[P1]** **Populate `CLAUDE.md` with real content — it is currently a
  redirect.** Created 2026-08-06 so the knowledge bundle could reach a Claude Code
  session at all (`okf_discover.py` refuses to call a repo wired when the only
  briefing file is one Claude Code never reads). It carries the bundle import and a
  sentence pointing at `AGENTS.md`, which means **none of the repo's actual rules
  are loaded content for Claude Code** — not the mirror contract, not the "this repo
  is public" warning, not the `Never:` list. That gap predates the file; the file
  only made it visible.
  Do NOT fix it by symlinking to `AGENTS.md`: `managing-agent-instructions` bans
  symlinked briefing files, and `okf_discover.py` demotes a shared `CLAUDE.md` to
  inline mode, so the two runtimes would stop getting one copy each. Copy the rules
  across by hand, per the standalone-files mandate, keeping anything genuinely
  agy-specific out of `CLAUDE.md`.

## P2 — Nice-to-Have

- [ ] **[P2]** **Fix `run_eval.py` so it can measure a skill that is also
  installed.** It injects a uniquely-named command file and counts only calls to
  that name, but the real plugin skill wins the call, so every positive scores 0.00
  and a correct description reads as a total triggering failure. Measured
  2026-08-06; full account and the workaround in
  `.agents/wiki/evals/run-eval-scores-an-installed-skill-as-a-miss.md`. The fix is
  small — accept any `Skill` call and compare against the plugin-qualified name —
  and it matters because `run_loop.py` inherits the defect and would iterate a
  description toward nothing, unattended. Note the negatives are unaffected, so a
  broken run looks half-plausible rather than obviously wrong.

- [ ] **[P2]** **Settle the eval field name: `assertions` or `expectations`.**
  `skill-creator-enhanced/references/schemas.md` defines `expectations` and
  `grading.json` consumes that name (the viewer depends on it), but `SKILL.md:239`
  tells the author to see schemas.md "including the `assertions` field", which
  schemas.md does not document. The repo now has one of each:
  `gcloud/evals/evals.json` uses `assertions`, `prompt-design/evals/evals.json` uses
  `expectations`. Pick the schema's name, fix the SKILL.md sentence, and migrate the
  odd one out — a grader reading the wrong key silently grades nothing.

- [ ] **[P2]** **Re-run `prompt-design`'s description optimization at a sample size
  that can answer it.** Attempted 2026-08-06 and **inconclusive, not negative** — two
  candidates scored 14/20 and 16/20, which looks like a result and is not: their mean
  positive trigger rates were identical to three decimals (0.500 / 0.500) while 4 of
  10 positives flipped by ≥0.66, and the additive candidate, which contains the
  shipped opening sentence verbatim, scored 0.33 where the shipped text scored 1.00
  on that sentence's own case. The shipped description was kept. Everything needed to
  resume is in `prompt-design/evals/trigger_optimization/` (20-query set, three result
  files, README); the reasoning and the sizing are in
  `.agents/wiki/evals/three-runs-per-query-cannot-separate-two-descriptions.md`.
  **Budget before promising an answer:** judge on aggregate positive trigger rate,
  not per-query pass/fail, at ~10 runs per query — roughly 200 nested `claude -p`
  sessions per candidate. Do the `run_eval.py` fix above first, or this measures
  nothing. The over-triggering half is already settled: every near-miss held at 0.00
  across all three runs, so no further work is needed there.

- [ ] **[P2]** **Add the `skill-creator-enhanced` near-miss to `prompt-design`'s
  trigger eval set.** The 2026-08-06 set covers the in-repo competitors
  (`new-prompt`, `optimizing-prompts-w-vertex`) but nothing probing the boundary with
  `skill-creator-enhanced` — "write me a skill description that triggers reliably" is
  prompt work by any reasonable reading and is currently tested neither way. Decide
  which skill owns it before adding the case.
