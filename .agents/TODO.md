# TODO

Backlog for the skills themselves. Not synced to the plugin — the mirror only
takes top-level directories containing a `SKILL.md`, and the `*/` glob does not
match dot-directories.

## P2 — Nice-to-Have

- [ ] **[P2]** **Two eval prompts name `refresh-skills`, which no longer exists.**
  `skill-improvement/evals/evals.json` ("Review my SKILL.md in
  active-skills/refresh-skills…") and `skill-portfolio-review/evals/evals.json`
  ("Consolidate git-sync and refresh-skills…") were written against a skill removed
  2026-08-06, so both cases now point at a directory that isn't there and cannot be
  run as written. Repoint them at a skill that still exists — `git-sync` is the
  natural substitute in both, since it was the other half of the consolidation the
  second prompt describes.



- [ ] **[P2]** **`skill-creator-enhanced` does not fire on rewording an existing
  skill description.** Its description advertises "optimize a skill's description
  for better triggering accuracy", but "my pdf-extract skill isn't firing on
  invoices — reword the description so it triggers reliably, and check the new
  wording does better" fired **no skill at all**, 3/3 runs, live mode, 2026-08-06,
  Claude Code 2.1.x. The adjacent case (*write* a description for a new skill, plus
  test cases) fires it 3/3, so the create half works and the improve half does not.
  `skill-improvement` is the other candidate owner and also did not fire — decide
  which of the two should claim rewording before editing either description. The
  regression test is already in place: the last two queries of
  `prompt-design/evals/trigger_optimization/eval_set.json`, with the measurement in
  that directory's README.

- [ ] **[P2]** **Write assertions for `git-sync` and `show-context`.** Both ship an
  `evals/evals.json` with well-formed eval cases and an empty `assertions` list on
  every one (3 and 4 cases respectively), so a benchmark run over either grades
  nothing and reports a vacuous 100%. Every other skill with evals has them. Needs
  someone who knows what correct behaviour looks like for those two skills —
  `SKILL.md` wants the user to sign off on assertions, so draft and confirm rather
  than inventing them. Found 2026-08-06 while normalizing the eval schema.

- [ ] **[P2]** **Re-run `prompt-design`'s description optimization at a sample size
  that can answer it.** Attempted 2026-08-06 and **inconclusive, not negative** — two
  candidates scored 14/20 and 16/20, which looks like a result and is not: their mean
  positive trigger rates were identical to three decimals (0.500 / 0.500) while 4 of
  10 positives flipped by ≥0.66, and the additive candidate, which contains the
  shipped opening sentence verbatim, scored 0.33 where the shipped text scored 1.00
  on that sentence's own case. The shipped description was kept. Everything needed to
  resume is in `prompt-design/evals/trigger_optimization/` (now a 22-query set, three
  result files, README); the reasoning and the sizing are in
  `.agents/wiki/evals/three-runs-per-query-cannot-separate-two-descriptions.md`.
  **The tooling is now ready** (2026-08-06): `run_loop.py` runs without an API key,
  selects on aggregate positive trigger rate, and refuses to start underpowered.
  Design: `docs/designs/2026-08-06-trigger-eval-redesign.md`.
  ```bash
  claude plugin disable active-skills        # else probe runs are contaminated
  cd skill-creator-enhanced && python -m scripts.run_loop \
    --eval-set ../prompt-design/evals/trigger_optimization/eval_set.json \
    --skill-path ../prompt-design --runs-per-query 20 --min-effect 0.10 \
    --results-dir ../prompt-design/evals/trigger_optimization/runs
  ```
  Preflight quotes the budget before spending: ~200 sessions per iteration, up to 5
  iterations. **Re-enable the plugin afterwards.** The three stored result files
  predate the two added negatives and cannot be compared against a new run without
  re-baselining. The over-triggering half is already settled: every near-miss held
  at 0.00 across all three runs, so no further work is needed there.
