# Design: Agent-eval skill set — `agent-eval-design` / `agent-eval-implement` / `agent-eval-run`

**Status:** Implemented — trigger-eval gate still to run (tracked in `.agents/TODO.md`)
**Author:** Claude (with Matt Larkin)
**Date:** 2026-08-06

> **Implementation notes, 2026-08-06.** All three skills authored as specified
> (SKILL.md + the planned reference files each; probe sets stored as
> `<skill>/evals/trigger_eval.json`, 7 positive + 7 negative per skill). All
> mechanical gates pass: ship check, frontmatter check, codename scrub, and a
> model-ID scrub. Deviations from the design as written: (1) Open question 1 is
> resolved — the contaminated source doc was removed from the repo per Matt's
> instruction (relocated to the session scratchpad, never committed; the
> references to it below are citations of that now-removed file). (2) One
> attribution in the source-material assessment was too pessimistic: the
> rubric-based criteria (`rubric_based_final_response_quality_v1`,
> `rubric_based_tool_use_quality_v1`) are public ADK eval criteria backed by the
> Vertex Gen AI Evaluation Service, not internal-only — no scrub-list impact.
> (3) The verified ADK surface is richer than designed: `adk conformance` and
> user simulation exist and are covered in `adk-evalsets.md`.

> **Placement note.** This file lives in `docs/designs/` because everything inside a
> skill directory ships to users via the mirror, and repo-root `DESIGN.md` is reserved
> for the design-system spec. `docs/` has no `SKILL.md`, so the sync skips it. Do not
> move this file into a skill directory.

## Problem

The repo has no skills covering agent evaluation — how to decide what to measure for
a GCP-hosted AI agent, how to build the eval assets, and how to run them locally, in
CI/CD, and in production. The raw material exists as `docs/agent-eval-how-to.md`, a
4,774-line compendium of overlapping research passes that no agent can usefully load
at task time. This design distills it into three shippable skills that give
step-by-step guidance for **designing**, **implementing**, and **running** agent
evals on the GCP Agent Platform, and it must be executable as an implementation spec
without re-reading the source doc.

Note the domain distinction that shapes everything below: these skills evaluate
**GCP AI agents** (ADK / Vertex AI / Gemini Enterprise). The repo's existing
`skill-creator-enhanced` evaluates **Claude Code skills** (trigger probes). The two
vocabularies overlap ("run evals", "eval set", "measure performance"), so trigger
separation is a first-class design concern, not an afterthought.

## Source-material assessment

`docs/agent-eval-how-to.md` is several deep-research outputs concatenated: each topic
appears 3–5 times in variant form. The durable methodology, deduplicated:

- **EDD lifecycle** ("quality flywheel"): define "good" before building; offline
  evals in CI → gated deploy → observe → online evals → convert production failures
  into permanent golden test cases.
- **Levels of analysis:** end-to-end, step-level, trajectory. Trajectory = the full
  record of reasoning, tool calls, and observations.
- **Metric taxonomy:** outcome (task success rate, factual correctness, CSAT);
  trajectory/tool-use (tool selection & parameter accuracy, trajectory match,
  efficiency); RAG (faithfulness, answer relevancy, context precision/recall);
  operational (latency, cost/tokens, tool-call reliability); quality & safety
  (hallucination, policy adherence, adversarial robustness).
- **Scorer types:** code-based rules; LLM-as-judge against a rubric (with the
  judge-model-diversity rule: don't judge an agent with its own model family);
  human-in-the-loop as gold standard and judge calibration.
- **Golden dataset methods:** curate from production traces (sampling strategies,
  PII scrubbing, failure→test conversion); manual authoring by SMEs (critical user
  journeys, golden trajectories, unanswerable questions); synthetic generation
  (LLM role-play, seed-and-expand, back-translation).
- **Adversarial testing:** direct and indirect prompt injection, jailbreak
  role-play, OWASP LLM Top 10 coverage.
- **CI/CD quality gates:** candidate-vs-baseline comparison with statistical tests
  (McNemar for paired pass/fail, paired t-test or Wilcoxon for continuous/ordinal
  metrics, bootstrap CIs), explicit pass/fail thresholds, automated go/no-go.
- **Online evals:** shadow mode, asynchronous sampling and scoring, dashboards,
  anomaly detection, failure-to-regression-test flywheel.
- **Third-party frameworks:** RAGAS, TruLens, DeepEval, LangSmith.

**The doc is contaminated with internal-only codenames.** It names an "AI Agent
Evaluation Service (AES)", "Everest", "Hydra", "EvalHub", "Universal (Agent)
Autorater", a `lamda.Example` proto, "Spanner Queue", and "Gemini Data Studio" — and
one research pass admits (line 284) these "were not found in public documentation."
This repo is public; none of these names may ship in a skill. See the scrub list
under Cross-cutting concerns. Its code samples also pin stale model IDs — do not
copy any model ID from the doc into a skill.

## Public tool surface

Verified against live Google Cloud docs on 2026-08-06 (google-developer-knowledge
MCP; sources: `cloud.google.com/gemini-enterprise-agent-platform/...` evaluate-agents,
optimize-agent, models/evaluation-agents; `adk.dev/evaluate`):

| Capability | Public tool | Entry point |
| :--- | :--- | :--- |
| Local eval of ADK agents | ADK evaluation | `adk eval` CLI; evalset JSON files; pytest integration; ADK Web UI for capturing sessions as eval cases |
| Instruction optimization | ADK | `adk optimize` (iterates root instructions against a test suite) |
| Programmatic final-response + trajectory eval | Vertex AI Gen AI evaluation service | Vertex AI SDK (`vertexai.Client`, docs call it the Agent Platform SDK); `pip install google-cloud-aiplatform[adk,evaluation]` |
| Managed/console evals | Gemini Enterprise Agent Platform | Console (Agent Platform → Agents page); ground-truth datasets in Cloud Storage or BigQuery |
| Deploy/manage evaluated agents | Agent Engine | Agent Engine templates (incl. LangChain template) |
| Production monitoring | Agent observability (Cloud Observability) | tracing, logging, metrics for deployed agents |
| RAG / third-party | RAGAS, DeepEval, TruLens, LangSmith | open-source; RAGAS configurable to use Vertex AI models |

The exact SDK surface is moving (naming is already in flux in Google's own docs), so
skills carry **stable concepts + entry points** and instruct a live doc lookup
(google-developer-knowledge MCP first, then context7) for exact signatures at use
time. See Key decisions.

## Skill-set overview & granularity rationale

Three skills, one per lifecycle moment, sharing an `agent-eval-` prefix:

| Skill | Moment | Core question |
| :--- | :--- | :--- |
| `agent-eval-design` | Before any eval code exists | What should we measure, with what scorers, against what dataset? |
| `agent-eval-implement` | Plan in hand, writing assets | How do I build evalsets, eval code, judges, and datasets on GCP? |
| `agent-eval-run` | Assets in hand, operating | How do I execute, gate, analyze, and extend to production? |

**Why three and not one umbrella skill.** The umbrella test asks whether the pieces
are ever invoked independently. They are: "what metrics should I use for my agent" is
a planning conversation with no code; "wire my evals into Cloud Build" arrives weeks
later in a different session. The three tool surfaces barely overlap (methodology
prose vs. SDK/evalset authoring vs. CLI/CI/statistics). And the material is too large
for one skill: a single SKILL.md would immediately push everything into references,
recreating the routing problem one level down. Naming carries the seam: distinct
verbs and objects per description, shared prefix for discoverability.

**Why not more than three.** The obvious fourth (dataset construction) is inseparable
from design — metric choice dictates dataset shape — so it stays a section plus a
reference file in `agent-eval-design`. This portfolio was consolidated 34→14 skills
one day ago [ASSUMED: unjustified proliferation remains a standing concern]; three is
the floor implied by the user's own enumeration, and the fallback (below) merges
implement+run if trigger evals show the seam is invisible to routing.

## Skill spec: `agent-eval-design`

**Name:** `agent-eval-design` (kebab-case, operation-named, no gerund).

**Frontmatter description (draft):**
> Design an evaluation strategy for a GCP AI agent before writing any eval code —
> choose metrics across outcome, trajectory, operational, and safety dimensions;
> pick scorer types (code-based rules, LLM-as-judge, human review); and plan a
> golden dataset with adversarial coverage. Use when the user asks how to evaluate
> an ADK, Vertex AI, Agent Engine, or Gemini Enterprise agent, what metrics to use,
> how to build a golden or test dataset for an agent, or wants an eval plan or eval
> strategy. Not for evaluating Claude Code skills (skill-creator-enhanced), writing
> eval code (agent-eval-implement), or executing evals (agent-eval-run).

**Trigger boundaries.** Fires on planning-vocabulary + agent-domain anchors
("evaluate my agent", "metrics", "golden dataset", "eval strategy"). Must NOT fire
on: authoring/executing requests (siblings); "measure my skill's trigger accuracy"
(skill-creator-enhanced); "optimize this prompt" (optimizing-prompts-w-vertex);
"create/manage an Agent resource" or "run a conversation via the Interactions API"
(gemini-agents-api / gemini-interactions-api — they operate agents, never evaluate
them). The latter three are no longer authored here but remain installed from the
plugin, so they still compete for routing on this machine.

**SKILL.md outline** (~120 lines, step-by-step):
1. Establish context — agent's task, tools, RAG or not, risk profile.
2. Choose levels of analysis (end-to-end / step-level / trajectory) and offline vs
   online scope.
3. Select metrics from the taxonomy — table with "use when" column; RAG metrics only
   for RAG agents.
4. Choose scorers per metric — rules vs LLM-as-judge vs HITL decision table;
   judge-model-diversity rule.
5. Plan the golden dataset — three sourcing methods, coverage checklist (happy path,
   edge, unanswerable, adversarial), sizing, versioning-as-code.
6. Set thresholds and baselines — what "good" is, before building (EDD).
7. Output: a written eval plan (template provided) that agent-eval-implement consumes.

**references/:** `metric-taxonomy.md` (full catalog with definitions),
`golden-dataset-methods.md` (trace curation, SME authoring, synthetic generation,
PII rules), `adversarial-testing.md` (injection taxonomy, OWASP LLM Top 10 mapping).

**scripts/:** none — nothing here is mechanical.

**Trigger-eval plan.** Positives: "how should I evaluate my customer-support agent
on Agent Engine", "what metrics for my ADK agent's tool use", "help me build a golden
dataset for my Vertex agent", "design an eval strategy for our RAG agent", "define
quality thresholds before we build the agent". Negatives: "write the evalset JSON for
my agent" (implement), "run adk eval in CI" (run), "run evals to test my skill" and
"benchmark my skill's description" (skill-creator-enhanced), "optimize my agent's
prompt with Vertex" (optimizing-prompts-w-vertex).

## Skill spec: `agent-eval-implement`

**Name:** `agent-eval-implement`.

**Frontmatter description (draft):**
> Turn an agent eval plan into runnable assets on GCP — author ADK evalset files and
> pytest evals, write Vertex AI Gen AI evaluation service code for final-response and
> trajectory metrics, build custom LLM-as-judge rubrics, and prepare ground-truth
> datasets in Cloud Storage or BigQuery for Agent Platform console evaluations. Use
> when the user wants to write, code, build, or create agent evals, evalset files,
> custom judge metrics, or eval datasets for an ADK, Vertex AI, Agent Engine, or
> Gemini Enterprise agent. Not for choosing metrics or planning datasets
> (agent-eval-design) and not for executing runs or CI/CD gating (agent-eval-run).

**Trigger boundaries.** Fires on authoring verbs + eval-asset nouns. Must NOT fire
on metric-selection questions (design), execution/analysis (run), or Claude Code
skill authoring ("create a skill" → skill-creator-enhanced — the anchor is *agent
eval assets*, never "skill").

**SKILL.md outline** (~130 lines):
1. Start from an eval plan (if none, invoke agent-eval-design first — explicit
   cross-pointer).
2. Author ADK evalsets — evalset JSON structure, capturing real sessions via ADK Web
   UI, unit-style pytest evals; when evalsets suffice vs. when to escalate to the
   evaluation service.
3. Wrap the agent for programmatic eval — runnable/wrapper pattern; Agent Engine and
   LangChain-template agents.
4. Configure Vertex AI Gen AI evaluation service metrics — final-response and
   trajectory metric configuration via the Vertex AI SDK; verify exact signatures
   with a live doc lookup (MCP) rather than trusting memorized API shapes.
5. Build custom LLM-as-judge scorers — rubric authoring rules (anchored scales,
   one quality per rubric), pointwise vs pairwise, judge-model diversity, calibrating
   the judge against a small human-labeled set.
6. Prepare datasets — schema for ground truth incl. reference trajectories; upload
   to Cloud Storage/BigQuery for console evals; version datasets like code.
7. Smoke-test one case end-to-end before writing the full suite.

**references/:** `adk-evalsets.md` (file format, capture flow, pytest wiring),
`vertex-eval-service.md` (dataset schema, metric config, wrapper patterns),
`custom-judges.md` (rubric templates, calibration procedure),
`third-party-frameworks.md` (RAGAS with Vertex AI models, DeepEval, TruLens,
LangSmith — optional, one file).

**scripts/:** none in v1 [ASSUMED: nothing is mechanical enough yet; schema
validators would duplicate what `adk eval` already reports].

**Trigger-eval plan.** Positives: "write an evalset for my ADK agent", "implement
trajectory evaluation with the Vertex AI SDK", "create a custom LLM judge for my
agent's responses", "build the eval dataset and upload it to BigQuery for agent
evaluation", "add pytest evals for my agent". Negatives: "what metrics should I
use" (design), "run the evals and compare to baseline" (run), "create a new skill
for X" (skill-creator-enhanced), "write unit tests for my Python service" (none).

## Skill spec: `agent-eval-run`

**Name:** `agent-eval-run`.

**Frontmatter description (draft):**
> Execute and operationalize agent evals on GCP — run adk eval locally, wire evals
> into CI/CD with statistical quality gates, compare candidate vs baseline agent
> versions, analyze failed trajectories and eval results, and extend evaluation to
> production with online evals and observability. Use when the user wants to run
> agent evals, add agent evals to a CI/CD pipeline, gate deployment on eval results,
> debug eval regressions or failed trajectories, or monitor deployed agent quality.
> Not for choosing metrics (agent-eval-design), authoring evalsets or eval code
> (agent-eval-implement), or measuring Claude Code skills (skill-creator-enhanced).

**Trigger boundaries.** Fires on execution/operations vocabulary + agent anchors.
The dangerous collision is "run evals" alone, which also describes
skill-creator-enhanced's benchmark loop — the description therefore always pairs the
verb with *agent*/pipeline/deployment nouns, and the negative probes test the bare
phrase explicitly.

**SKILL.md outline** (~140 lines):
1. Run locally — `adk eval` CLI against evalsets; reading per-case and aggregate
   results; `adk web` for interactive inspection.
2. Handle non-determinism — multiple runs per case; never gate on a single run;
   choose the statistical test by metric type (McNemar for paired pass/fail, paired
   t-test or Wilcoxon for continuous/ordinal, bootstrap CIs for ratios); interpret
   p-values and confidence intervals; a CI containing zero means no detected change.
3. Wire into CI/CD — trigger on PR (Cloud Build; cross-pointer to
   cloud-build-triggers skill), pin dataset versions, candidate-vs-baseline
   comparison, explicit thresholds, automated go/no-go that blocks merge.
4. Analyze results — console eval pages, trajectory ("flight recorder") reading:
   find the first bad step, not the last; cluster failures by pattern before fixing.
5. Improve — `adk optimize` for instruction refinement; convert every confirmed
   production failure into a permanent golden test case.
6. Extend to production — shadow-mode deployment, async sampling and scoring of live
   sessions, agent observability dashboards, anomaly alerts; the offline↔online
   flywheel.

**references/:** `statistical-gates.md` (test-selection table, worked examples,
threshold-setting guidance), `cicd-integration.md` (Cloud Build wiring, dataset
pinning, baseline management), `online-evals.md` (shadow mode, async scoring
architecture, failure-to-test flywheel).

**scripts/:** `eval_gate.py` deferred to a later phase [ASSUMED] — a stdlib-only
candidate-vs-baseline gate (reads two results JSONs, runs the right test, exits
non-zero on significant regression) is genuinely mechanical, but shipping it means
maintaining a stats tool in every user's install; defer until the prose version
proves insufficient.

**Trigger-eval plan.** Positives: "run the evals for my ADK agent", "add agent evals
to our Cloud Build pipeline", "did the new agent version regress against baseline",
"analyze why this agent trajectory failed the eval", "set up online evals for the
deployed agent". Negatives: "design the eval metrics" (design), "write the evalset"
(implement), "run evals to test my skill" and "benchmark skill performance"
(skill-creator-enhanced), "set up a Cloud Build trigger for my container build"
(cloud-build-triggers).

## Cross-cutting concerns

**Internal-codename scrub (hard gate).** None of the following may appear in any
skill directory: `AES`, `AI Agent Evaluation Service`, `Everest`, `Hydra`,
`EvalHub`, `EvalRun`, `Universal Autorater`, `Universal Agent Autorater`,
`lamda.Example`, `Spanner Queue`, `Gemini Data Studio`, `ADK sampler`. Pre-push
check, run from repo root (case-insensitive, skill dirs only):

```bash
grep -riE '\bAES\b|Everest|Hydra|EvalHub|Autorater|lamda\.|Spanner Queue|Data Studio' \
  agent-eval-design/ agent-eval-implement/ agent-eval-run/ && echo LEAK || echo clean
```

Where the doc used an internal name for a real capability, the skill names the
public equivalent instead (dataset service → Cloud Storage/BigQuery datasets;
autorater → LLM-as-judge via the evaluation service; eval UI → Agent Platform
console evaluation pages) or describes the *pattern* without a product name
(async online-eval queue).

**Model-version policy.** No Gemini model ID appears anywhere in the three skills —
not in prose, not in code samples (the source doc pins several stale ones). Skills
say "current Pro/Flash tier; look up the current model ID" per the standing rule.

**Doc-lookup instruction.** Each skill's SKILL.md includes one line directing exact
API signatures to a live lookup (google-developer-knowledge MCP first, context7
second) — the product surface is changing faster than skill content should.

**Repo conventions.** Each skill is a root-level `<name>/SKILL.md` with its
references inside its own directory (everything in it ships); no version fields; no
design docs inside skill dirs; frontmatter passes the awk check in CLAUDE.md;
authoring findings that cost investigation go to `.agents/wiki/`, not TODO.

## Key decisions

| Decision | Choice | Alternatives considered | Rationale |
| :--- | :--- | :--- | :--- |
| Granularity | 3 skills, `agent-eval-` prefix | 1 umbrella skill; 2 (design+build / run) | Independently invoked lifecycle moments; disjoint tool surfaces; umbrella would overflow into references and recreate routing internally. Fallback: merge implement+run if portfolio evals can't separate them. |
| Tool grounding | Public surface only | Follow the doc's names | Repo is public; the doc itself concedes its service names aren't publicly documented; unverifiable APIs would ship hallucination-bait. |
| Volatile API detail | Concepts + entry points in references; live MCP lookup for signatures | Bake full SDK snippets | Naming already in flux in Google's docs; baked snippets rot silently, a lookup instruction doesn't. |
| Skill-vs-skill collision | Domain anchors in every description + explicit "not for" cross-pointers | Rely on distinct verbs alone | "run evals" is shared vocabulary with skill-creator-enhanced; verbs alone demonstrably under-separate (see trigger-eval-redesign findings). |
| Third-party frameworks | One optional reference file in agent-eval-implement | Omit; or a fourth skill | Doc coverage is real and users ask for RAGAS by name, but it's not the primary GCP path. |
| Scripts | None in v1; stats gate deferred | Ship `eval_gate.py` now | Shipped scripts are a maintenance surface in every install; prose + existing CLI output may suffice. |

## Risks and trade-offs

- **Trigger separation is the main risk.** Three sibling descriptions plus
  skill-creator-enhanced share eval vocabulary. Mitigations: agent-vs-skill anchor
  nouns, "not for" cross-pointers, and a portfolio-level trigger eval before ship.
  Known harness limits apply (see `.agents/wiki/evals/`): ≥5 runs per probe — 3
  cannot separate descriptions — and probes must run from a clean project root with
  the installed plugin disabled, or every positive scores as a miss.
- **Staleness.** The Agent Platform is being renamed under our feet. Trade-off
  accepted: less copy-pasteable detail in exchange for content that doesn't rot;
  each reference file carries a "verified as of" date.
- **Leak risk.** The scrub gate covers the three skill dirs; the contaminated source
  doc must never move into one (see Open questions for its fate).
- **Optimizes for routing precision over installation size:** three directories,
  ~10 reference files. Acceptable — references load lazily.

## Implementation plan

Each phase ships independently; a lone skill is useful without its siblings.

1. **`agent-eval-design`** — author via skill-creator-enhanced's creation flow;
   distill the three reference files from the source doc (dedup pass); frontmatter
   awk check; scrub grep; trigger eval (positives + negatives above, ≥5 runs, clean
   root).
2. **`agent-eval-implement`** — same flow; verify every named API entry point against
   live docs via MCP at authoring time; add cross-pointer to design.
3. **`agent-eval-run`** — same flow; portfolio trigger eval across all three new
   skills plus skill-creator-enhanced negatives; if implement/run can't be separated,
   execute the fallback merge before shipping either.
4. **Ship** — run the CLAUDE.md ship-check loop (each new dir must list as `ship`),
   push, confirm the sync `::notice::` shows all three; sweep for accidental
   references to the source doc.

**Testing strategy** is the trigger-eval plan embedded in each spec (the repo's
existing harness, per the 2026-08-06 trigger-eval-redesign), plus the two mechanical
gates (frontmatter awk, scrub grep). No unit tests — v1 ships no scripts.

## Open questions

1. **Fate of `docs/agent-eval-how-to.md`.** Currently untracked, 400 KB, and
   contains internal codenames. Recommendation: do **not** commit it; once the three
   skills are authored, delete it or park it outside the repo [ASSUMED: it was
   dropped in as one-time source material, not as a document to publish]. Needs
   Matt's call before any commit sweep picks it up.
2. **Console-flow depth.** Specs above treat code-first (ADK + SDK) as primary and
   the Gemini Enterprise console flow as secondary [ASSUMED]. If Matt's team works
   console-first, agent-eval-implement steps 2–4 rebalance.
3. **Judge calibration.** Is a human-labeled calibration set realistic for Matt's
   agents, or should custom-judges.md soften that step to optional?
4. **`eval_gate.py`.** Deferred [ASSUMED]; revisit after first real CI integration
   shows whether prose guidance suffices.
