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
         "hook_installed": False, "ci_installed": False, "manual_surfaces": 0,
         "head": sh("git rev-parse --short HEAD"),
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
            surf = re.search(r"<!-- manual-surfaces.*?-->", head, re.S)
            if surf:
                state["manual_surfaces"] = len(
                    re.findall(r"^\s*[0-9a-f]{40}\s+\S", surf.group(0), re.M))
        tdir = cfg.get("tickets_dir", "docs/tickets")
        if os.path.isdir(tdir):
            state["tickets"] = len([f for f in os.listdir(tdir) if f.startswith("TICKET-")])
        # The file on disk, not the config's claim about it: a workflow
        # deleted since setup should read as absent, not installed.
        ci = cfg.get("ci") if isinstance(cfg.get("ci"), dict) else {}
        state["ci_installed"] = os.path.exists(
            ci.get("workflow") or ".github/workflows/manual-guard.yml")
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
