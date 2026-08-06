# TODO

Backlog for the skills themselves. Not synced to the plugin — the mirror only
takes top-level directories containing a `SKILL.md`, and the `*/` glob does not
match dot-directories.

## P0 — Address Immediately

- [ ] **[P0]** **Push the 2026-08-06 skill removals — held on
  `feat/remove-agent-workflow-skills`, not merged to `main`.** Twenty skills were
  removed (`using-agent-workflow` and the workflow-methodology set it indexed:
  `writing-plans`, `executing-plans`, `subagent-driven-development`,
  `test-driven-development`, `systematic-debugging`, `verification-before-completion`,
  `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`,
  `using-git-worktrees`, `dispatching-parallel-agents`, `brainstorming`, `grill-me`,
  `handoff`, `explanatory-mode`, `skill-portfolio-review`, `optimizing-prompts-w-vertex`,
  `gemini-interactions-api`, `google-cloud-recipe-auth`). The sync is `rsync --delete`,
  so pushing removes all twenty from every installed user with no deprecation window,
  and `/writing-plans`, `/systematic-debugging`, and the rest start returning nothing.
  The shipping set drops from 34 skills to 14. Push when that is intended — or say
  "push anyway".

## P2 — Nice-to-Have

- [ ] **[P2]** **`project-setup`'s evals test behaviour the skill has never had.**
  Three assertions in `project-setup/evals/evals.json` require the agent to clone
  `https://github.com/mlarkin00/agent-memory` into the project root *before*
  invoking `managing-agent-instructions` ("Clones agent-memory", "Seeds Before
  Docs", "Seeds Memory Despite Deprioritization"), but `project-setup/SKILL.md`
  does not mention `agent-memory` anywhere and `git log -S agent-memory --
  project-setup/SKILL.md` returns nothing — it was never there. So the cases fail
  as written. Decide which side is right: either add the memory-seeding step to the
  skill, or drop those assertions. Found 2026-08-06 during the dangling-reference
  sweep; unrelated to the skill removals.

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
  cd skill-creator-enhanced && python -m scripts.run_loop \
    --eval-set ../prompt-design/evals/trigger_optimization/eval_set.json \
    --skill-path ../prompt-design --runs-per-query 20 --min-effect 0.10 \
    --results-dir ../prompt-design/evals/trigger_optimization/runs --verbose
  ```
  Do **not** run `claude plugin disable active-skills` first. Probe isolation is
  automatic per-invocation via `--settings`; disabling the plugin globally would
  also remove `new-prompt` and `skill-creator-enhanced`, which are exactly the
  competitors the near-miss queries exist to test against. (`optimizing-prompts-w-vertex`
  was the third such competitor and was removed 2026-08-06 — see the eval set's
  README on query 11.) Preflight quotes the
  budget and waits for confirmation: ~200 sessions per iteration, up to 5. If a run
  is aborted, sweep leftovers with `python -m scripts.run_eval --cleanup`. The three
  stored result files predate the two added negatives and cannot be compared against
  a new run without re-baselining. The over-triggering half is already settled:
  every near-miss held at 0.00 across all three runs, so no further work is needed
  there.
