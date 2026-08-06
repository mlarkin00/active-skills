# Design: Trigger-eval loop for `skill-creator-enhanced`

**Status:** Implemented and verified — all phases complete
**Author:** Claude (with Matt Larkin)
**Date:** 2026-08-06

> **Implementation notes, 2026-08-06.** Phase 4 was absorbed into Phase 3: the
> history structure changed completely, so `generate_html()` was dead code the
> moment the loop was rewired, and leaving it would have shipped a broken report.
> Three things the design got wrong, all corrected in place below: the
> `--output-format json` shape, the need for `stdin=DEVNULL`, and the assumption
> that the shorten step could be a third conversational turn. One gap the design
> missed entirely: `--mode live` cannot evaluate a candidate description at all,
> so the loop now measures the baseline once and stops rather than reporting
> `inconclusive` forever for a reason unrelated to the candidates.

> **Placement note.** This file is deliberately *not* `skill-creator-enhanced/DESIGN.md`
> (everything inside a skill directory ships to users via the mirror) and *not*
> repo-root `DESIGN.md` (that filename is reserved for the design-system spec in the
> `google/design.md` format — see `managing-agent-instructions`). `docs/` has no
> `SKILL.md`, so the sync skips it. Do not "fix" this by moving the file.

## Context

`skill-creator-enhanced` ships a description-optimization loop: measure whether a
skill's description causes the skill to trigger, propose a better description, repeat.
Two independent defects make it unusable.

**It cannot run here.** `run_loop.py` and `improve_description.py` import `anthropic`
and construct `anthropic.Anthropic()`, requiring the SDK and `ANTHROPIC_API_KEY`.
Neither is present, and this box authenticates Claude Code through OAuth, so there is
no key to fall back on. `anthropic` is the *only* missing dependency in the entire
skill — every other script is stdlib (plus `yaml`, which is installed).

**What it optimizes is noise.** The loop feeds on per-query pass/fail against a 0.5
trigger-rate threshold at 3 runs per query. Measured 2026-08-06 on `prompt-design`:
two candidate descriptions produced mean positive trigger rates identical to three
decimal places (0.500 vs 0.500) while 4 of 10 positives flipped by ≥0.66. The
decisive control: the additive candidate contains the shipped description's opening
sentence **verbatim** and still scored 0.33 where the shipped text scored 1.00 on the
query that sentence names almost word for word.

These must be fixed together. Fixing only the first — swapping the transport so the
loop runs — produces something strictly worse than the status quo: an unattended
process that rewrites a working description on the strength of four coin flips, with
nothing in the loop able to notice. The runnability defect is currently the only
thing preventing that.

## Landscape

### What exists

| Component | Lines | Runs? | Notes |
| :--- | ---: | :--- | :--- |
| `scripts/run_eval.py` | 447 | **Yes** | Shells out to `claude -p`. Fixed 2026-08-06: live/probe modes, contamination accounting, records which skill fired. |
| `scripts/run_loop.py` | 352 | **No** | `import anthropic` at module scope; fails before the first eval. |
| `scripts/improve_description.py` | 248 | **No** | Same. Builds a plain-text prompt, then calls the API. |
| `scripts/aggregate_benchmark.py` | 401 | Yes | Benchmark half. Stdlib only. |
| `scripts/generate_report.py` | 326 | Yes | HTML report for the loop. |
| `agents/{grader,comparator,analyzer}.md` | 721 | Yes | Benchmark half, agent-orchestrated prose. |
| `eval-viewer/`, `assets/` | 2364 | Yes | Benchmark half. |

Out of ~3,800 lines, the broken surface is two files and one import.

### Constraints the codebase imposes

- **Everything in a skill directory ships to users.** The mirror takes top-level
  directories containing a `SKILL.md` and rsyncs them wholesale. Dev-only files must
  live in `.agents/` or `docs/`, which the `*/` glob does not match.
- **Stdlib only, in practice.** Every script that runs today is stdlib + `yaml`.
  Adding a dependency is what broke the loop in the first place; the design must not
  add another.
- **Nothing is versioned here.** No manifest, no version field.

### The measurement, stated properly

Aggregate positive trigger rate over `n = runs_per_query × n_positives` Bernoulli
observations. Comparing two arms, the 95% minimum detectable effect at p≈0.5 is

```
MDE ≈ 1.96 × sqrt(2 × 0.25 / n)
```

| runs/query | n per arm | MDE (95%) | sessions per arm |
| ---: | ---: | ---: | ---: |
| 3 (current default) | 30 | **0.253** | 30 |
| 5 | 50 | 0.196 | 50 |
| 10 | 100 | 0.139 | 100 |
| 20 | 200 | 0.098 | 200 |
| 30 | 300 | 0.080 | 300 |

At the shipped default of 3 runs, two descriptions must differ by **25 percentage
points of positive trigger mass** before the difference is readable. The 2026-08-06
attempt reported a "2-point win" (16/20 vs 14/20) on a real difference of 0.000. This
table is the single most important output of the design: it converts "how many runs?"
from a taste question into a budget decision, and it shows the current default cannot
answer the question the loop exists to ask.

### Adjacent platform work

`claude plugin eval` exists in the CLI and covers the *benchmark* half natively —
`--ablation with-without`, `--judge-model`, `--report`, `--runs`, `--threshold`. It is
gated: every invocation prints `` `plugin eval` is currently in early access `` and
exits 0 without doing anything. It does **not** cover trigger measurement, which is
what this design addresses. Two consequences: do not build on it yet, and do not
invest further in the benchmark half, which it will likely obsolete.

## Requirements

### Functional

1. The loop runs on a box with no `ANTHROPIC_API_KEY` and no `anthropic` package.
2. Candidate selection is made on **aggregate positive trigger rate**, not per-query
   pass/fail.
3. The loop refuses to declare a winner when the observed difference is inside the
   noise floor for the configured sample size.
4. Before spending anything, the loop reports its MDE and session count, and stops if
   the configuration cannot detect an effect worth acting on.
5. The loop detects that the skill under test is already installed and says so, rather
   than silently measuring nothing.
6. Train/test holdout is preserved, so a description tuned on one query set is scored
   on another.

### Non-functional

- **No new third-party dependencies.** Stdlib only.
- **Cost is stated in sessions, up front.** A nested `claude -p` session is the unit
  of spend; the user approves a number before the run starts.
- **Reproducible verdicts.** Given a results JSON, the accept/reject decision is
  recomputable without re-running anything.

### Constraints

- Must serve both audiences (see below) from one code path.
- Ships to users: cannot depend on this machine's paths, plugins, or auth.
- No files added inside `skill-creator-enhanced/` that users should not receive.

### Audience: both, with the conflict made explicit

The skill ships to general skill authors, but this repo's maintainer keeps hitting a
case they never will.

| | New-skill author (default) | This repo's maintainer |
| :--- | :--- | :--- |
| Skill under test installed? | No | Yes, via marketplace |
| Probe mode | Clean | Contaminated — installed copy wins the call |
| Competitors present | Whatever they have | The real overlapping set |

The design treats "already installed" as a **detected condition that switches
behaviour and announces itself**, not as an assumption either way. Detection is a
filesystem check (plugin cache dirs and `~/.claude/skills/`), so it is cheap and
deterministic and costs no sessions.

### Out of scope

- The benchmark half — grader, comparator, analyzer, viewer, `aggregate_benchmark.py`.
  It runs today and the platform is moving to own it.
- Migrating anything to `claude plugin eval`.
- Actually re-running `prompt-design`'s optimization. That is a separate budgeted job
  tracked in `.agents/TODO.md`.

### Open questions

1. **What effect size is worth detecting?** The design proposes 0.10 as the default
   floor (≈20 runs/query, 200 sessions/arm). A larger floor is cheaper and answers
   less. This is a budget call, not a technical one.

*(Resolved 2026-08-06: the report is markdown, written to a path, with no browser —
see Reporting below.)*

## Design

### Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │            run_loop.py                  │
                    │  ┌───────────────────────────────────┐  │
   eval_set.json ──▶│  │ PREFLIGHT                         │  │
   skill dir     ──▶│  │  · installed-skill detection      │  │
                    │  │  · MDE + session count            │  │
                    │  │  · abort if MDE > --min-effect    │  │
                    │  └────────────────┬──────────────────┘  │
                    │                   ▼                      │
                    │  ┌───────────────────────────────────┐  │
                    │  │ MEASURE ── run_eval.run_eval()    │──┼──▶ claude -p ×N
                    │  │  returns per-query trigger rates  │  │    (subprocess)
                    │  └────────────────┬──────────────────┘  │
                    │                   ▼                      │
                    │  ┌───────────────────────────────────┐  │
                    │  │ DECIDE ── stats.compare()         │  │
                    │  │  aggregate rate + CI vs incumbent │  │
                    │  │  → improved | inconclusive | worse│  │
                    │  └────────────────┬──────────────────┘  │
                    │                   ▼                      │
                    │  ┌───────────────────────────────────┐  │
                    │  │ PROPOSE ── propose.py             │──┼──▶ claude -p ×1
                    │  │  (only when not inconclusive)     │  │    (subprocess)
                    │  └───────────────────────────────────┘  │
                    └─────────────────────────────────────────┘
```

The change in shape from today: a **PREFLIGHT** gate that can refuse to start, and a
**DECIDE** step that sits between measuring and proposing. Today measurement feeds
proposal directly, with per-query pass/fail as the connective tissue.

### Components

**`scripts/stats.py`** *(new, ~80 lines, stdlib `math` only)*

The only new file. Pure functions, no I/O, trivially testable — which matters because
every accept/reject verdict in the system routes through it.

```python
def aggregate_rate(results: list[dict]) -> tuple[float, int]:
    """Positive-query trigger rate and observation count.

    Weights by observations, not by query, so a query that lost runs to
    contamination contributes proportionally less rather than distorting the mean.
    """

def mde(n_obs: int, p: float = 0.5, z: float = 1.96) -> float:
    """Minimum detectable effect between two arms of n_obs each."""
    return z * math.sqrt(2 * p * (1 - p) / n_obs)

def compare(incumbent: tuple[float, int], candidate: tuple[float, int],
            z: float = 1.96) -> dict:
    """-> {verdict: improved|inconclusive|worse, delta, ci, mde}"""
```

`p=0.5` is the conservative choice: it maximises Bernoulli variance, so the MDE
reported is the worst case for any true rate. A design that estimated `p` from the
data would report a smaller, flattering MDE exactly when rates are extreme.

**`scripts/propose.py`** *(replaces `improve_description.py`'s transport)*

The prompt `improve_description.py` builds is plain text with no tool use, no
streaming, and no structured output. Nothing about it requires the SDK.

```python
def call_claude(prompt, model=None, timeout=300, cwd=None) -> dict:
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.run(cmd, capture_output=True, env=env, cwd=cwd,
                          timeout=timeout, stdin=subprocess.DEVNULL)
    messages = json.loads(proc.stdout)          # a LIST, not an object
    final = [m for m in messages if m.get("type") == "result"][-1]
    return {"text": final["result"], "cost_usd": final.get("total_cost_usd")}
```

**Corrected against the real CLI, 2026-08-06 (Claude Code 2.1.x).** An earlier draft
of this design had `json.loads(stdout)["result"]`. That is wrong: `--output-format
json` emits a JSON **array** of messages (`system/init`, `assistant`,
`rate_limit_event`, `result`), and the text lives on `result` of the last message
whose `type` is `result`. That message also carries `is_error`, `total_cost_usd`,
and `duration_ms` — the cost field is what lets preflight quote a real budget rather
than a session count. `stdin=subprocess.DEVNULL` is required: without it the CLI
waits 3 seconds for stdin on every call.

Measured: **$0.20 and ~4.2s per proposing session.** One proposal per iteration, so
the propose step is negligible against the measurement step — a 20-runs/query
iteration is 200 eval sessions against 1 proposing session.

This is the same transport `run_eval.py` already uses, including the `CLAUDECODE`
strip that permits nesting. The existing prompt-construction and
response-parsing code is kept verbatim; only the call is swapped.

Two consequences worth stating. It inherits the user's Claude Code auth, so it works
under OAuth — the point of the change. And the proposing model is now the same one
the user runs interactively, which makes the loop's suggestions representative of
what they will actually experience.

**`scripts/run_eval.py`** *(extended)*

Add to `summary`: `positive_rate`, `positive_observations`, `mde`. All derivable from
data it already produces — no behavioural change, no extra sessions. Per-query
`trigger_rate`, `contaminated`, and `fired` already exist as of 2026-08-06.

**`scripts/generate_report.py`** *(HTML → markdown)*

Today this emits a self-contained HTML page and `run_loop.py` writes it to a temp
file, injects `<meta http-equiv="refresh" content="5">`, and calls
`webbrowser.open()`. That is a design for someone watching a browser tab while a
long job runs, and in practice nobody does — the report is never viewed.

Replace `generate_html(data, auto_refresh, skill_name)` with
`generate_markdown(data, skill_name)`. The module name is already format-neutral, so
it stays. Drop `import webbrowser` and the auto-refresh injection from `run_loop.py`
entirely.

The report is still rewritten in place after every iteration, so a long run can be
watched with `cat`, `tail -f`, or an editor that reloads. It loses nothing by not
being HTML and gains being readable over SSH, diffable between runs, greppable, and
committable next to the results JSON.

```markdown
# Description optimization — prompt-design

Mode `probe` · 10 positives × 20 runs · MDE 0.098 · 2026-08-06 17:04 UTC
Exit: **inconclusive after 3 iterations** (patience 2/2)

## Verdict

Kept the **incumbent** description. No candidate cleared the detection floor.

## Iterations

| # | Positive rate | 95% CI | Δ vs incumbent | MDE | Verdict |
|--:|--------------:|:-------|---------------:|----:|:--------|
| 0 | 0.500 | 0.431–0.569 | — | — | incumbent |
| 1 | 0.615 | 0.548–0.682 | +0.115 | 0.098 | **improved** |
| 2 | 0.640 | 0.573–0.707 | +0.025 | 0.098 | inconclusive |
| 3 | 0.590 | 0.522–0.658 | −0.025 | 0.098 | inconclusive |

## Per-query detail — iteration 1

| Query | Rate | Fired instead |
|:------|-----:|:--------------|
| Write me a prompt I can paste into Gemini… | 1.00 | — |
| Turn this into something a model will follow… | 0.35 | `new-prompt` ×7 |

## Descriptions

### Iteration 1 (adopted)
> Use this skill whenever the user wants a prompt built…
```

The "Fired instead" column is the diagnostic the HTML report never carried and the
one that actually explains a low rate: a positive scoring 0.35 because a *competing*
skill wins it is a different problem from one scoring 0.35 because nothing fires.
`run_eval.py` has recorded this per run since 2026-08-06; nothing consumed it.

**`scripts/run_loop.py`** *(rewired)*

Preflight, then the measure/decide/propose cycle above. Loses `webbrowser` and the
temp-file report path.

### Interface Design

```bash
python -m scripts.run_loop \
  --eval-set <path> --skill-path <path> \
  --runs-per-query 20 \          # was 3
  --min-effect 0.10 \            # new: refuse to run if MDE exceeds this
  --max-iterations 5 \
  --patience 2 \                 # new: stop after N inconclusive iterations
  --report <path.md> \           # markdown; 'none' to disable. was: HTML + browser
  [--force] [--yes]              # new: bypass the gate / skip confirmation
```

`--report` defaults to `report.md` inside `--results-dir` when that is set, and to
`none` otherwise. The old default wrote an HTML file to `tempfile.gettempdir()` and
opened a browser whether or not one existed.

Preflight output, before anything is spent:

```
Skill:        prompt-design
Mode:         probe  (candidate descriptions are not installed)
WARNING:      'prompt-design' is installed via active-skills@mlarkin00-plugins.
              Probe runs it will win are unmeasurable. Disable it first:
                  claude plugin disable active-skills
              ...or use --mode live to measure only the shipped description.

Positives:    10 queries × 20 runs = 200 observations per arm
Detectable:   0.098 (95% CI)  ≤ --min-effect 0.10  OK
Budget:       200 sessions per iteration, up to 5 iterations = 1000 sessions

Proceed? [y/N]
```

Per-iteration verdict:

```
Iteration 2   candidate: 0.615 [0.548-0.682]   incumbent: 0.500
              delta +0.115  >  MDE 0.098   → IMPROVED, adopting

Iteration 3   candidate: 0.640 [0.573-0.707]   incumbent: 0.615
              delta +0.025  <  MDE 0.098   → INCONCLUSIVE, keeping incumbent
              (patience 1/2)
```

`INCONCLUSIVE` is the verdict the current system cannot express, and it is the one
the 2026-08-06 run actually warranted.

### Key Decisions

| Decision | Choice | Alternatives considered | Rationale |
| :--- | :--- | :--- | :--- |
| Propose-step transport | `claude -p` subprocess | Install `anthropic` + provision an API key; Vertex AI Prompt Optimizer | The SDK path needs a key this box cannot have (OAuth-only) and would need one on every user's box too. `claude -p` is already the transport `run_eval.py` uses and inherits the user's auth. Vertex authenticates via ADC and would work here, but optimizes instruction-following, cannot observe trigger rate, and its skill forbids agent-authored steering hints — so it cannot close a loop. |
| Selection signal | Aggregate positive trigger rate | Per-query pass/fail (current); precision/recall/F1 | Pass/fail discretizes a rate into a coin flip at n=3 and was measured producing 0.500 vs 0.500 as "16/20 vs 14/20". F1 conflates the two error directions, and over-triggering is already settled at 0.00 across the negative set — the open question is one-sided. |
| Handling a difference inside the noise floor | Explicit `inconclusive` verdict; keep incumbent | Always adopt the higher score; adopt with a tiebreak | Adopting the higher score is exactly what turns run-to-run variance into a random walk across generations. "Inconclusive" is the honest state and, at the current default, the most common one. |
| Refusing to start | Preflight aborts when MDE > `--min-effect` | Warn and continue; no check | A run that cannot detect the effect it is looking for spends real money to produce a number that will be misread as a result. The 2026-08-06 attempt is the worked example. `--force` exists for deliberate exploration. |
| Variance assumption | Fixed `p=0.5` | Estimate `p` from observed data | `p=0.5` maximises variance, so the reported MDE is a worst case. Estimating `p` reports a smaller MDE precisely when rates are extreme and the estimate is least stable. |
| Installed-skill detection | Filesystem scan, warn, offer both exits | Auto-disable the plugin; fail hard; ignore | Auto-disabling mutates the user's environment as a side effect of running an eval — unacceptable. Failing hard blocks the legitimate live-mode path. Detection costs nothing and both audiences get an accurate message. |
| Report format | Markdown file, rewritten in place each iteration | Keep HTML + `webbrowser.open()`; HTML gated behind a TTY check; terminal-only output | The HTML report is never viewed — it was built for someone watching an auto-refreshing browser tab during a long run, which is not how this is used. Markdown is readable over SSH, diffable between runs, greppable, and commits next to the results JSON. A TTY check would have kept 326 lines of HTML generation alive to serve a workflow nobody wants. |
| Benchmark half | Leave untouched | Rebuild; delete; port to `claude plugin eval` | It runs. `claude plugin eval --ablation with-without` covers the same ground and is gated today — building against it strands the skill, and rebuilding it by hand is work the platform is about to discard. The same never-viewed argument applies to its `eval-viewer/viewer.html` (1,592 lines), but that is a separate call and out of scope here. |
| New-file footprint | One new module (`stats.py`) | Inline the math in `run_loop.py` | Every verdict routes through this math. Isolated pure functions can be unit-tested without spawning a session; inlined, they can only be tested by spending money. |

### Patterns

**Preflight gate.** A cheap deterministic check that can refuse an expensive
irreversible operation, run before any spend. Adapted here in one respect: it reports
its own statistical power, so the refusal is derived from the configuration rather
than from a hardcoded threshold.

**Verdict object over boolean.** `compare()` returns
`improved | inconclusive | worse` rather than "is the candidate better?". The
system's central failure was a two-valued answer to a three-valued question — the
missing value being "the data cannot say".

## Risks and Trade-offs

**Nested-session lifecycle (added after the design was written)**

Every run spawns a real `claude -p` session that bills for as long as it lives,
three levels down: `run_loop.py` → pool worker → `claude`. Killing the parent does
not kill them. Pool shutdown lives in the parent's `atexit`, which a signal skips,
and the workers are separate processes that outlive it still holding their
children. Observed 2026-08-06: SIGKILL to `run_loop.py` left **11 nested sessions
running and billing**, re-parented away and invisible — they had to be killed by
explicit PID. This is worst exactly when it matters most: the reaction to "this is
costing more than I expected" is Ctrl-C, and Ctrl-C is when up to
`--num-workers` sessions keep going.

Fixed in `run_eval.py`: each session gets its own process group
(`start_new_session=True`) so the whole subtree is reaped as a unit — `claude`
spawns its own children, and killing only the direct child leaves those running.
The group is registered module-side, and `SIGINT`/`SIGTERM`/normal exit all reap
the registry. The reaper installs at import so it is present in pool workers,
which is where the sessions actually live.

SIGKILL is uncatchable by anyone, so PIDs are also appended to a pidfile and
`python -m scripts.run_eval --cleanup [--dry-run]` sweeps whatever survived. The
pidfile is removed on clean exit.

The sweep's guard needed two attempts and the failure is instructive. Matching
`"claude" in cmdline and " -p " in cmdline` matched **the shell that invoked the
sweep** — `/tmp/claude-.../` supplied "claude" and `ps -p $PID` supplied " -p ".
Requiring `argv[0]` to be claude then rejected real sessions, because a shebang
wrapper makes the kernel rewrite `argv[0]` to the interpreter. The guard that
holds: some argument must be *exactly* named `claude`, `-p` must be present as its
own argument, and the sweep never signals itself or any ancestor. A cleanup tool
that sends SIGKILL on a substring match is worse than no cleanup tool.

**What could go wrong**

- **`claude -p` returns prose instead of a description.** The existing parsing in
  `improve_description.py` already handles this (regex extraction with fallback);
  keep it and fail the iteration rather than adopting a malformed description.
- **Cost surprise.** 20 runs/query × 10 positives × 5 iterations = 1000 sessions.
  Mitigated by preflight confirmation, but the honest headline is that a conclusive
  answer is expensive and the design makes that visible rather than cheap-looking.
- **Contamination detection drifts.** Plugin cache layout is not a stable contract.
  If the filesystem scan silently stops matching, probe runs get contaminated again.
  Mitigated by `run_eval.py`'s existing per-run contamination accounting, which
  catches it empirically even when detection misses — belt and braces, deliberately.
- **The design assumes wording is what moves triggering.** The verbatim-sentence
  control (0.33 vs 1.00 on identical text) is unexplained and may indicate position
  or interaction effects. If it reproduces at 20 runs, the whole A/B framing is wrong
  and no amount of sampling fixes it. **This is the largest open risk**, and the
  design surfaces it rather than resolving it: `inconclusive` verdicts accumulating
  against clearly-different candidates is the signal to stop and investigate.

**What we are trading off**

Optimizes for *not shipping a false positive*, at the cost of iteration speed and
money. A loop that mostly answers "inconclusive" is less satisfying than one that
always names a winner, and it is correct more often. Given the output is a
description that ships to every user of a skill, that is the right direction.

**At 10x**

Ten skills to optimize makes per-skill session cost the binding constraint. The
lever is a shared negative set — over-triggering is cheap to measure and already
settled — plus sequential testing (stop as soon as the CI excludes zero) rather than
fixed-n runs. Both are additive to this design; neither is worth building now.

**Security**

`propose.py` shells out with `subprocess.run(cmd_list)` — no shell interpolation, so
a description containing shell metacharacters is inert. The description under test
is attacker-influenced only if the user is optimizing a description they did not
write. `run_eval.py` writes probe command files into `.claude/commands/` under the
project root and deletes them in a `finally` block; the filename is a UUID and the
content is author-supplied. Unchanged by this design, noted because it is the one
place the loop writes into the user's project.

## Implementation Approach

### Phases

Each phase is independently testable and leaves the skill working.

**Phase 1 — `stats.py` + `run_eval.py` reporting.** Add the module and surface
`positive_rate` / `mde` in the eval summary. Nothing consumes the verdict yet.

Verifiable with zero sessions against the three stored `eval_results_*.json` files in
`prompt-design/evals/trigger_optimization/`. **Already run, 2026-08-06** — this is
the design's premise, and it reproduces:

```
eval_results_1_shipped-description.json    rate=0.400  n=30  (10 positives)
eval_results_2_rewrite-candidate.json      rate=0.500  n=30
eval_results_3_additive-candidate.json     rate=0.500  n=30

shipped  vs rewrite    delta=+0.100  MDE=0.253  -> INCONCLUSIVE
shipped  vs additive   delta=+0.100  MDE=0.253  -> INCONCLUSIVE
rewrite  vs additive   delta=+0.000  MDE=0.253  -> INCONCLUSIVE
```

The reported "2-point win" (16/20 vs 14/20) is +0.100 against a detection floor of
0.253 — less than half the effect needed to be readable. The two candidates that
differed most in wording are separated by exactly 0.000. These three lines are the
regression test for `stats.py`: if `compare()` ever returns anything but
`INCONCLUSIVE` for all three pairs, it is wrong.

**Phase 2 — `propose.py`.** Swap the transport. Verifiable in one session: feed it a
fixed results JSON and confirm it returns a description string. This is the phase
that makes the loop runnable at all.

**Phase 3 — `run_loop.py` rewiring.** Preflight, verdicts, patience. Verifiable
end-to-end at `--runs-per-query 3 --force --max-iterations 1` for a cheap smoke test
(30 sessions), which should report `inconclusive` for almost anything — the correct
answer at that sample size.

**Phase 4 — markdown report.** Swap `generate_html()` for `generate_markdown()`,
drop `webbrowser`, rewire `--report`. Verifiable with zero sessions by rendering a
stored `results.json` from a previous run.

**Phase 5 — `SKILL.md` and `references/schemas.md`.** Document the new flags, the MDE
table, the installed-skill condition, and the markdown report. Retire the "run each
query 3 times to get a reliable trigger rate" claim in the Step 3 prose, which is the
sentence that originated the error. Also remove the "it opens an HTML report in the
browser" promise in the same section.

### Testing Strategy

| Level | What | Cost |
| :--- | :--- | :--- |
| Unit | `stats.py` — MDE against hand-computed values; `compare()` verdicts at boundaries | free |
| Regression | Replay stored `eval_results_*.json`; assert `inconclusive` | free |
| Regression | Render a stored `results.json` to markdown; assert tables present | free |
| Integration | `propose.py` returns a parseable description | 1 session |
| Smoke | `run_loop.py` at `--runs-per-query 3 --max-iterations 1 --force` | ~30 sessions |
| Acceptance | The `prompt-design` re-run, at the budget the preflight quotes | 200+/arm |

The first two tiers are free and cover the reasoning that broke. There is currently
no test directory in this repo and no test runner; the unit tests should be plain
`assert` statements in `if __name__ == "__main__"` inside `stats.py`, consistent with
the repo's existing script style, rather than importing a framework nothing else uses.

### Migration Plan

No data migration — the eval-set format is unchanged and `run_eval.py`'s output gains
fields without losing any. The behavioural break is the default `--runs-per-query`
moving from 3 to 20, which changes the cost of an unmodified command by ~7x. That
must not happen silently: the preflight confirmation is what makes it safe, and
`--yes` exists for scripted use.

`improve_description.py` is kept as a thin wrapper delegating to `propose.py` for one
release, since `SKILL.md` references it by name and users may have it in scripts.

## Appendix: what this does not fix

The loop will still be expensive, and for skills whose descriptions are already
good it will mostly return `inconclusive`. That is the correct behaviour and it is
worth stating plainly, because the failure mode of this design is a user concluding
the tool is broken when it is in fact reporting that their description is fine.
`SKILL.md` should say so directly.
