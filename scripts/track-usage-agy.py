#!/usr/bin/env python3
"""PostToolUse hook (Antigravity) — increment the counter for a skill.

Antigravity has no skill-activation tool. Activating a skill *is* reading its
SKILL.md, so a skill use appears as an ordinary file read whose path lands in
the runtime's skills directory:

    {"stepIdx": 4,
     "toolCall": {"name": "view_file",
                  "args": {"AbsolutePath": ".../skills/guidelines/SKILL.md"}}}

That path points at the runtime's flat skills directory, where every plugin's
skills are merged together. The name is taken from there, but membership is
decided against this plugin's own skills/ — so skills belonging to other
plugins are not counted, and no list of skill names has to be maintained.

Always exits 0. A tracker must never block a session.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import usage_lib  # noqa: E402

# Any ".../skills/<name>/SKILL.md". Anchored on the separator so a directory
# merely named "skills" deeper in a path cannot match a different layout.
SKILL_PATH = re.compile(r"(?:^|/)skills/([^/]+)/SKILL\.md$")

# Antigravity names the path argument differently per tool.
PATH_KEYS = ("AbsolutePath", "TargetFile", "file_path", "path", "Path")


def skill_from_path(value: str) -> str | None:
    if not value:
        return None
    match = SKILL_PATH.search(value.strip().strip('"'))
    return match.group(1) if match else None


def skill_from_tool_call(tool_call: dict) -> str | None:
    args = tool_call.get("args")
    if not isinstance(args, dict):
        return None
    for key in PATH_KEYS:
        name = skill_from_path(str(args.get(key) or ""))
        if name:
            return name
    return None


def skill_from_transcript(path: str, step_idx: object) -> str | None:
    """Fall back to the transcript when toolCall is absent.

    Older Antigravity builds delivered only stepIdx and transcriptPath; the
    docs still describe it that way. Reading the transcript keeps this hook
    working on those builds.
    """
    if not path or step_idx is None:
        return None
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("step_index") != step_idx:
                    continue
                for call in entry.get("tool_calls") or []:
                    if isinstance(call, dict):
                        name = skill_from_tool_call(call)
                        if name:
                            return name
    except OSError:
        return None
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if not isinstance(payload, dict):
        return 0

    tool_call = payload.get("toolCall")
    name = skill_from_tool_call(tool_call) if isinstance(tool_call, dict) else None
    if not name:
        name = skill_from_transcript(
            str(payload.get("transcriptPath") or ""), payload.get("stepIdx")
        )

    # Membership is a directory test against this plugin's own skills/, so a
    # skill shipped by some other plugin into the shared directory is ignored.
    if not name or not usage_lib.is_plugin_skill(usage_lib.normalize(name)):
        return 0

    usage_lib.increment(usage_lib.normalize(name))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BaseException:
        sys.exit(0)
