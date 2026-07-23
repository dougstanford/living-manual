#!/bin/sh
# state.sh [repo-root] — one JSON line describing setup state.
# The manual skill runs this first and branches on it instead of probing
# the repo with repeated tool calls.
cd "${1:-.}" || exit 1
python3 - <<'EOF'
import json, os, subprocess

def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""

state = {"configured": False, "config": None, "manual_exists": False,
         "hook_installed": False, "manual_base": None, "head": sh("git rev-parse --short HEAD"),
         "tickets": 0, "claude_md_wired": False}

if os.path.exists(".living-manual.json"):
    try:
        cfg = json.load(open(".living-manual.json"))
        state["configured"] = True
        state["config"] = cfg
        manual = cfg.get("manual_path", "docs/USER_MANUAL.html")
        if os.path.exists(manual):
            state["manual_exists"] = True
            head = open(manual).read(4000)
            import re
            m = re.search(r"manual-base: ([0-9a-f]+)", head)
            if m: state["manual_base"] = m.group(1)
        tdir = cfg.get("tickets_dir", "docs/tickets")
        if os.path.isdir(tdir):
            state["tickets"] = len([f for f in os.listdir(tdir) if f.startswith("TICKET-")])
    except Exception as e:
        state["config_error"] = str(e)

# Worktree-safe: .git may be a file pointing elsewhere.
hook = sh("git rev-parse --git-path hooks/pre-push")
if hook and os.path.exists(hook) and "living-manual" in open(hook).read():
    state["hook_installed"] = True
for cm in ("CLAUDE.md", ".claude/CLAUDE.md"):
    if os.path.exists(cm) and "living-manual" in open(cm).read():
        state["claude_md_wired"] = True
        break
print(json.dumps(state))
EOF
