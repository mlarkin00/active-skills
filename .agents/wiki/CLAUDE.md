# active-skills — OKF Bundle

An OKF v0.1 knowledge bundle. It holds the **runtime evidence** behind this repo's
rules: facts that cost investigation to establish about the environment these
skills are developed and measured in.

## Domain

Not the skills' content. The skills are the product and carry their own guidance —
the `design.md` linter's `color-mix` false positive, for example, is documented
inside `managing-agent-instructions/SKILL.md` because a user who installs that
skill needs it and never sees this bundle.

This bundle covers the layer underneath: how this repo is built, evaluated, and
published, and what breaks when you try. Evals, tooling, and publishing mechanics.

## Directory structure

```
.agents/wiki/
├── index.md          # auto-generated root catalog — do not edit by hand
├── CLAUDE.md         # this file
└── evals/            # measuring skills: triggering, benchmarks, harness behaviour
```

## Type vocabulary

- `Pitfall` — something that fails, silently or misleadingly, and how it presents
- `Runtime Behaviour` — how a tool or runtime actually behaves, as measured
- `Convention` — a decision made here whose rationale would otherwise be re-litigated

## What belongs here

| Layer | Answers | Lifecycle |
| :--- | :--- | :--- |
| `AGENTS.md` (repo root) | "What rules must I follow on day one?" | Rewritten; kept short |
| a skill's `SKILL.md` | "What should an agent using this skill do?" | Ships to users |
| **this bundle** | "**Why** is it this way? What did we try? What broke?" | Append-only |
| `.agents/TODO.md` | "What still needs doing?" | Open tasks only |

**Scope test:** a fact belongs here if it cost investigation to establish and is
not derivable from the files in this repo. A skill's own guidance does not — it
ships with the skill.

## Authoring conventions

- **`type` is required.** Always also write `title` and `description`.
- **Descriptions are the product.** The description is what a future session reads
  in the index before deciding to open the doc. Make it a **claim, not a topic**.
- **One concept per doc.** If a doc needs two titles, it is two docs.
- **Evidence over assertion.** State the command, the measurement, the symptom.
- **Version-pin anything time-sensitive.** "Measured 2026-08-06 against Claude Code
  2.1.x", not "apparently".
- **Cross-links are file-relative**, never absolute.

## Discoverability — do not remove this

This repo has **no `CLAUDE.md`** — only `AGENTS.md`. Claude Code never reads
`AGENTS.md`, and `agy` reads it but does not expand `@` imports, so an
`@.agents/wiki/index.md` line there would fire for nobody. The catalog is therefore
**inlined** into `AGENTS.md` between `<!-- llm-wiki:discovery -->` markers.

**If that block is deleted, this bundle stops being read.**

The inlined form is a **copy** and goes stale on every added, renamed, or deleted
concept. Refresh and check it with:

```bash
L=~/.claude/plugins/cache/mlarkin00-plugins/llm-wiki/<version>
python3 $L/scripts/okf_index.py    .agents/wiki           # regenerate index.md
python3 $L/scripts/okf_discover.py .agents/wiki           # refresh the inlined block
python3 $L/scripts/okf_discover.py .agents/wiki --check   # exit 1 if missing or stale
python3 $L/scripts/okf_validate.py .agents/wiki           # §9 conformance
```

Or the slash commands, which do the same: `/llm-wiki:index`, `/llm-wiki:validate`.

## Maintenance

Regenerate the index and refresh discovery after any concept is added, renamed, or
deleted — the two are one step, and skipping the second leaves `AGENTS.md`
advertising a catalog that no longer matches the bundle.
