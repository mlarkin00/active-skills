---
type: Runtime Behaviour
resource: prompt-design/evals/trigger_optimization
title: Trigger evals at 3 runs per query cannot separate two skill descriptions
description: Two candidate descriptions produced an identical mean positive trigger
  rate of 0.500 while 4 of 10 individual queries flipped by 0.66 or more, so the
  per-query pass/fail totals that skill-creator-enhanced reports are noise.
tags: [evals, triggering, measurement, statistics]
timestamp: '2026-08-06T03:15:00+00:00'
---

`run_eval.py` defaults to `--runs-per-query 3` and reports a per-query pass/fail
against a 0.5 trigger-rate threshold. Measured 2026-08-06 on `prompt-design` with
20 queries (10 positive, 10 near-miss), three descriptions, 3 runs each:

| Description | Total | Positives | Mean positive trigger rate |
| :--- | ---: | ---: | ---: |
| shipped | 14/20 | 4/10 | — |
| rewrite candidate | 16/20 | 6/10 | 0.500 |
| additive candidate | 14/20 | 4/10 | 0.500 |

The two candidates are indistinguishable in aggregate — 0.500 against 0.500 — while
per-query rates move by a mean of 0.467 and a maximum of 1.00, and 4 of 10 positives
flip by ≥0.66.

The decisive control: the additive candidate contains the shipped description's
opening sentence **verbatim**, and still scored 0.33 where the shipped text scored
1.00 on "Write me a prompt I can paste into Gemini…" — a case that sentence names
almost word for word. A difference that survives holding the text constant is not a
text effect.

## Why it matters

The totals invite exactly the wrong conclusion. 16/20 against 14/20 reads as a
2-point win, and shipping on it means adopting a description on the strength of four
coin flips. Worse, `run_loop.py` automates that judgement: it would accept the
"winner" and iterate from it, compounding noise across generations with nothing in
the loop that can notice.

Aggregate standard error at 3 runs × 10 positives is √(0.25/30) ≈ 0.09, so the
threshold for a believable difference is roughly ±0.18 — about two full queries'
worth. Nothing smaller than that is readable at this sample size.

## What to do instead

Judge on the **aggregate positive trigger rate**, not per-query pass/fail, and size
the run to the effect worth detecting. Ten runs per query (100 observations) brings
the standard error to ~0.05; that is ~200 nested `claude -p` sessions per candidate
at 20 queries, which is the real price of a conclusive answer and should be budgeted
before promising one.

The negative half needs none of this. Every near-miss held at 0.00 across all three
runs except `/new-prompt` at 0.33 twice — over-triggering is cheap to measure and
was never in doubt. When the question is "is this description too broad", 3 runs is
enough; when it is "is candidate B better than A", it is not.

See [run_eval.py scores an installed skill as a miss](run-eval-scores-an-installed-skill-as-a-miss.md)
for the harness defect that has to be worked around before any of this measures
anything at all.
