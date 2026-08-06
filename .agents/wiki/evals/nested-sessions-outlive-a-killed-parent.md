---
type: Pitfall
resource: skill-creator-enhanced/scripts/run_eval.py
title: Killing an eval runner leaves its nested claude -p sessions running and billing
description: Pool workers are separate processes that survive the parent, so the
  finally blocks that terminate nested sessions never execute and up to
  --num-workers sessions keep running invisibly after the run is aborted.
tags: [evals, process-management, cost, claude-cli]
timestamp: '2026-08-06T18:35:00+00:00'
---

Work is spawned three levels deep, and the bottom level costs money for as long
as it lives:

```
run_loop.py  (parent)
  └── ProcessPoolExecutor  →  N worker processes
        └── subprocess.Popen(["claude", "-p", ...])   ← a billable session
```

Cleanup lived in the worker's `finally: process.kill()`, which only runs if the
worker's function unwinds. Kill the parent and it never does — `ProcessPoolExecutor`
shutdown lives in the *parent's* `atexit`, which a signal skips, and the workers
are independent OS processes that outlive it still holding their children.

Observed 2026-08-06, Claude Code 2.1.x: SIGKILL to `run_loop.py` left **11 nested
sessions running and billing**, re-parented away, with no output tying them to
the run that had apparently been cancelled. They had to be killed by explicit PID.

Reproduced with `sleep` standing in for `claude`, at no cost:

```
sleep children before kill: 6
parent alive? no
sleep children AFTER killing parent: 6      <- unchanged
their parent pid is now: 3021419            <- a surviving worker, not init
```

## Why it matters

This is worst exactly when it matters most. The design deliberately makes runs
expensive — preflight quotes 200 sessions per iteration — so the natural reaction
to "this is costing more than I expected" is Ctrl-C, and Ctrl-C is precisely when
up to `--num-workers` sessions keep going. The user believes the run stopped.

## The fix, and what each layer covers

| Signal | Catchable? | Covered by |
| :--- | :--- | :--- |
| Normal exit | — | `atexit` reaper |
| `SIGINT` (Ctrl-C), `SIGTERM` | yes | signal handler → reap registry |
| `SIGKILL` | **no** | pidfile + `--cleanup` sweep |

Each session spawns with `start_new_session=True` so the whole subtree is reaped
as a group — `claude` spawns its own children, and killing only the direct child
leaves those running. The reaper installs at *import*, so it is present in pool
workers, which is where the sessions actually live.

```bash
python -m scripts.run_eval --cleanup [--dry-run]
```

## The sweep's guard needed two attempts

A cleanup tool that sends `SIGKILL` off a PID file is dangerous, and both obvious
guards are wrong:

- `"claude" in cmdline and " -p " in cmdline` matched **the shell invoking the
  sweep** — `/tmp/claude-.../` supplied "claude" and `ps -p $PID` supplied " -p ".
- `Path(argv[0]).name == "claude"` rejected real sessions, because a shebang
  wrapper makes the kernel rewrite `argv[0]` to the interpreter, giving
  `["/bin/bash", "/path/to/claude", "-p", ...]`.

What holds: some argument must be *exactly* named `claude`, `-p` must be present
as its own argument, and the sweep never signals itself or any ancestor. Test it
by feeding it a pidfile containing PID 1 and your own PID.
