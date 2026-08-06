---
type: Pitfall
resource: .agents/wiki/publishing
title: Deep-research source docs name internal services in prose that no path scan catches
description: A 4,774-line research compendium dropped into this public repo named
  six unreleased internal services as if they were shipping products, and the
  repo's `google3`/`go/`/`blaze` path scan matches none of them; the doc's own
  text conceded the names were not publicly documented.
tags: [publishing, public-repo, disclosure, research-docs]
timestamp: '2026-08-06T22:55:00+00:00'
---

The repo's public-disclosure rule tells you to scan for internal **paths**
(`google3`, `go/`, `blaze`, `/google/bin/...`, `learning/gemini/...`). Prose
about internal *products* defeats that scan completely: the names are ordinary
capitalised English words sitting in fluent documentation-style sentences.

Observed 2026-08-06. `docs/agent-eval-how-to.md` — untracked, 400 KB, several
concatenated deep-research passes on agent evaluation — named, as though they
were public GCP products:

`AI Agent Evaluation Service (AES)` · `Everest` · `Hydra` · `EvalHub` ·
`Universal (Agent) Autorater` · `lamda.Example` (proto) · `Spanner Queue` ·
`Gemini Data Studio` · `ADK sampler`

None matches the path scan. Each reads as a product name a reader would assume
is documented somewhere.

The tell was inside the document itself. One research pass wrote, at line 284:

> While specific platforms named "AI Agent Evaluation Service (AES)" and "Everest
> framework" were not found in public documentation, the following provides a
> detailed walkthrough…

— and then continued using both names throughout the remaining ~4,000 lines as
if that caveat had settled the matter. Later passes dropped the caveat entirely
and presented `Hydra` and `EvalHub` as the platform's dataset and UI services.

## Why it matters

The document was one `git add` from being world-readable, with history. It
arrived as *source material for authoring*, which is exactly the framing under
which a file gets committed without disclosure review — it is "just research",
not code, and it contains no paths.

The second-order risk is worse: content distilled *out of* such a doc inherits
the names silently. Three skills were written from this one; without an explicit
scrub the codenames would have shipped inside `SKILL.md` prose to every plugin
user, where no reviewer would ever think to look for them.

## What to do

Treat any deep-research or LLM-generated compendium about Google-adjacent
tooling as unreviewed for disclosure until proven otherwise, regardless of file
type. Verify every product name against public documentation
(`google-developer-knowledge` MCP) rather than assuming a fluent sentence
implies a public product, and grep derived work for the specific names before
committing:

```bash
grep -riE '\bAES\b|Everest|Hydra|EvalHub|Autorater|lamda\.|Spanner Queue|Data Studio' <derived-dirs>/
```

Where an internal name denotes a real capability, name the public equivalent
instead — here: dataset service → Cloud Storage/BigQuery eval datasets;
autorater → LLM-as-judge via the Gen AI evaluation service; eval UI → Agent
Platform console evaluation pages — or describe the *pattern* with no product
name at all.

Resolution taken 2026-08-06: the source doc was moved out of the repo rather
than committed, and the three derived skills pass the grep above. Related:
verified public surface and the scrub gate are recorded in
`docs/designs/2026-08-06-agent-eval-skills.md`.
