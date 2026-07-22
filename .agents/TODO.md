# TODO

Backlog for the skills themselves. Not synced to the plugin — the mirror only
takes top-level directories containing a `SKILL.md`, and the `*/` glob does not
match dot-directories.

## P1 — Important / Unblocking

- [ ] **[P1]** Make an **OKF knowledge bundle the default store for project insights**, replacing the flat `.agents/INSIGHTS.md` that `managing-agent-instructions` currently prescribes. Proven on `mlarkin00/plugins` 2026-07-22; the change is to `managing-agent-instructions/SKILL.md` first, then the two skills that delegate to it.

  **The model.** A bundle at `<project_root>/.agents/wiki/`, OKF v0.1, managed by the `llm-wiki` plugin. One concept per fact. The project's `AGENTS.md` carries the *rules*; the bundle carries the *evidence* behind them — how each was established, against which version, and the symptom that exposed it. The briefing file then `@`-imports the generated root index:

  ```markdown
  Runtime evidence — how each rule below was established, and against which
  version — is an OKF bundle: `@.agents/wiki/index.md`
  ```

  **Why this beats a flat file — three reasons, in order of importance.**

  1. **Discoverability, which is the whole point.** `llm-wiki`'s own backlog carries a P1 recording that bundles go unread: in `local-minions` a pointer ("read `.agents/wiki/index.md` before re-deriving history") sat in context for a full session and the agent never opened it, because "I am about to re-derive history" is not a state an agent recognises about itself. An `@`-import is categorically different: it is **content the harness loads**, not prose the agent must decide to act on. That distinction is the finding — it is what makes the bundle worth keeping, and it is why the fix belongs in the skills rather than in `llm-wiki` alone.
  2. **It costs less context, not more.** The generated root index lists every concept by title. On `mlarkin00/plugins`: **823 bytes for 12 concepts**, against the 4,369-byte `INSIGHTS.md` it replaced — which was loaded whole, every session, relevant or not. Titles in context, bodies on disk, opened when relevant. Real progressive disclosure rather than the phrase.
  3. **Staleness becomes detectable.** Every claim is pinned to the version it was verified against. Runtime facts rot — that is their expected failure mode, not a hypothetical — and a flat file rots silently, whereas `/llm-wiki:lint` reports contradictions and stale claims. Where the bundle lives inside a repo that ships `llm-wiki`, its `PostToolUse` validator additionally blocks a malformed concept doc at write time (verified on both runtimes).

  **Scope test to carry into the skill** — a fact belongs in the bundle only if it **cost investigation to establish and is not derivable from the code**. Rules go in `AGENTS.md`; open work goes in `.agents/TODO.md`; the bundle is evidence. Without that test the bundle silently becomes a second, worse README.

  **Edits, by skill:**

  - `managing-agent-instructions/SKILL.md` — the load-bearing one.
    - Line 14 defines `.agents/INSIGHTS.md` as the "optional lessons log". Replace with the bundle as the default, INSIGHTS.md named only as the degraded fallback (see the open question below).
    - Add a phase alongside Phase 5 (TODO management) covering bundle lifecycle: when to mint a concept, the scope test, version-pinning claims, regenerate + validate after edits (`okf_index.py`, `okf_validate.py`), and periodic `lint` for staleness.
    - Phase 1 discovery: check for an existing bundle and for the `@`-import in the briefing file — a bundle with no import is the failure mode this item exists to prevent, and should be reported as drift.
    - Core Mandates: state that the `@`-import is mandatory whenever a bundle exists.
    - Gotchas table: *"I'll add a pointer sentence to CLAUDE.md so the agent knows about the wiki" → prose pointers were observed not firing; the import is the mechanism.*
  - `project-setup/SKILL.md` — line 40 lists `.agents/TODO.md` among scaffolded files; add the bundle, and add the `@`-import line to the generated `AGENTS.md`. Most of this follows automatically once `managing-agent-instructions` changes, since project-setup delegates to it — but the file list and the "Golden Path" section name files explicitly and will drift otherwise.
  - `close-session/SKILL.md` — Step 1's focus list routes *follow-up tasks* to `.agents/TODO.md`. Add the counterpart: a **durable lesson learned** becomes a concept in the bundle, not a TODO item. This session hit exactly that — five completed TODOs carried resolution notes worth keeping, and deleting the tasks would have deleted the evidence.

  **Open question that must be answered before implementing: how hard should the dependency on `llm-wiki` be?** These skills run in projects that will not have that plugin installed. Options: (a) bundle when `llm-wiki` is available, fall back to `.agents/INSIGHTS.md` otherwise — safest, but two shapes to document and the fallback will be what most projects get; (b) always scaffold the bundle, since the *format* is just markdown with YAML frontmatter and only `index`/`validate`/`lint` need the plugin — the `@`-import and the index can be hand-maintained; (c) make it unconditional and have `project-setup` offer to install `llm-wiki`. **(b) is the recommendation** — the model's value is the import plus the one-concept-per-fact discipline, and neither needs the tooling; the tooling makes it maintainable at scale. Decide explicitly and write the decision into the skill, rather than leaving each session to infer it.

  **Worked reference:** `mlarkin00/plugins@b77e3cf` — 12 concepts, 20 cross-links, 0 orphans, 0 broken links, 12/12 citation coverage, §9 conformant, with `.agents/wiki/CLAUDE.md` recording the scope test and stating that removing the `@`-import stops the bundle being read.

## P2 — Nice-to-Have

- [ ] **[P2]** Once the model above lands, reconcile it with `llm-wiki`'s own discoverability P1 — that item proposes a `SessionStart` hook to inject the root index. The `@`-import supersedes it for any host that supports briefing-file imports (Claude Code, Gemini CLI), so the hook should be documented as the fallback for hosts without them rather than the primary mechanism, and `/llm-wiki:init` should offer to write the import line into the host repo's briefing file. Filed against `llm-wiki` in `mlarkin00/plugins`; this is the skills-side half.
