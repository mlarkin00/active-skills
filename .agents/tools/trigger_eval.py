#!/usr/bin/env python3
"""Trigger eval against the REAL installed skill set.

run_eval.py injects a throwaway command file and checks whether the model
invokes *that* name. In an environment where the skill under test is also
installed as a plugin, the real skill wins the call and the probe never fires,
so every positive scores as a miss. This runs the query against the live skill
set instead and records which skill actually fired -- which is also the
measurement the competing-descriptions question needs.
"""

import argparse
import json
import os
import select
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


def run_once(query: str, cwd: str, timeout: int) -> str:
    """Return the name of the first skill invoked, or '' if none."""
    cmd = [
        "claude", "-p", query,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=cwd, env=env
    )

    buffer = ""
    pending_skill = False
    accumulated = ""
    start = time.time()
    try:
        while time.time() - start < timeout:
            if process.poll() is not None:
                rest = process.stdout.read()
                if rest:
                    buffer += rest.decode("utf-8", errors="replace")
                break
            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            if not ready:
                continue
            chunk = os.read(process.stdout.fileno(), 8192)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event.get("type") == "stream_event":
                    se = event.get("event", {})
                    t = se.get("type", "")
                    if t == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            if cb.get("name") == "Skill":
                                pending_skill = True
                                accumulated = ""
                            else:
                                # first tool call was something else
                                return ""
                    elif t == "content_block_delta" and pending_skill:
                        d = se.get("delta", {})
                        if d.get("type") == "input_json_delta":
                            accumulated += d.get("partial_json", "")
                    elif t == "content_block_stop" and pending_skill:
                        try:
                            return json.loads(accumulated).get("skill", "")
                        except json.JSONDecodeError:
                            # partial JSON -- salvage the skill field
                            marker = '"skill":'
                            if marker in accumulated:
                                tail = accumulated.split(marker, 1)[1].strip()
                                if tail.startswith('"'):
                                    return tail[1:].split('"', 1)[0]
                            return "?"
                    elif t == "message_stop":
                        return ""
                elif event.get("type") == "result":
                    return ""
        return ""
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", required=True)
    ap.add_argument("--skill", required=True, help="skill name counted as a trigger")
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--runs-per-query", type=int, default=3)
    ap.add_argument("--num-workers", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())

    futures = {}
    with ProcessPoolExecutor(max_workers=args.num_workers) as ex:
        for i, item in enumerate(eval_set):
            for r in range(args.runs_per_query):
                futures[ex.submit(run_once, item["query"], args.cwd, args.timeout)] = i

        fired: dict[int, list[str]] = {i: [] for i in range(len(eval_set))}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                fired[i].append(fut.result())
            except Exception as e:
                print(f"warn: run failed: {e}", file=sys.stderr)
                fired[i].append("<error>")

    results = []
    for i, item in enumerate(eval_set):
        names = fired[i]
        hits = sum(1 for n in names if args.skill in n)
        rate = hits / len(names) if names else 0.0
        should = item["should_trigger"]
        passed = rate >= 0.5 if should else rate < 0.5
        results.append({
            "query": item["query"],
            "should_trigger": should,
            "trigger_rate": rate,
            "fired": names,
            "pass": passed,
        })

    out = {
        "skill": args.skill,
        "runs_per_query": args.runs_per_query,
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["pass"]),
            "failed": sum(1 for r in results if not r["pass"]),
        },
    }
    Path(args.out).write_text(json.dumps(out, indent=2))

    print(f"{out['summary']['passed']}/{out['summary']['total']} passed")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        others = sorted({n for n in r["fired"] if n and args.skill not in n})
        extra = f"  -> {', '.join(others)}" if others else ""
        print(f"[{status}] rate={r['trigger_rate']:.2f} want={r['should_trigger']}: "
              f"{r['query'][:64]}{extra}")


if __name__ == "__main__":
    main()
