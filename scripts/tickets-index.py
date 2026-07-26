#!/usr/bin/env python3
"""tickets-index.py TICKETS_DIR MANUAL [--no-tracker]

Rebuilds the manual's TICKETS block from the ticket files themselves
(frontmatter + Summary section), so the queue index can never drift
from the directory. Tickets with status shipped or declined stay on
disk as the record and drop out of the index.

The directory is the record, but it is not the whole truth: an issue
can exist at the tracker with no local ticket file (filed straight in
the web UI, or written on a branch that never merged). Left alone the
queue fails open, telling a reader nothing is filed while the tracker
says otherwise. So after indexing the files this also asks the
configured tracker for its open issues and folds in any the local
files don't already reference, marked `origin: "tracker"`.

Only providers a script can reach are queried. GitHub goes through the
gh CLI. Jira lives behind the Atlassian MCP, which only a model session
can call, so Jira reconciliation belongs to the ticket skill and is
reported here rather than attempted. Every tracker failure (no gh, no
auth, offline, no config) degrades to the file-only index with a
warning; the rebuild itself never fails on it. `--no-tracker` skips the
query outright.
"""
import importlib.util, json, os, re, subprocess, sys

STATUSES = ("ready", "needs-answers", "shipped", "declined")

def load_sync(scripts_dir):
    spec = importlib.util.spec_from_file_location(
        "sync_index", os.path.join(scripts_dir, "sync-index.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def parse(path):
    """-> (index entry or None if resolved, tracker ref or None).

    The ref is read from every file, resolved or not: a shipped ticket
    still owns its tracker issue, and folding that issue back in as
    unqueued work would be a lie.
    """
    text = open(path).read()
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None, None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    ref = fm.get("issue") or fm.get("jira")  # jira: is the pre-0.2.4 name
    if fm.get("status") in ("shipped", "declined"):
        return None, ref
    target = fm.get("target", "current")
    sm = re.search(r"^## Summary\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    anchors = fm.get("anchors")
    anchors = ([a.strip() for a in anchors.split(",") if a.strip()] if anchors
               else re.findall(r"#([A-Za-z0-9_-]+)", fm.get("section", "")))
    return {
        "id": fm.get("id", os.path.basename(path)[:11]),
        "title": fm.get("title", "(untitled)"),
        "type": fm.get("type", "idea"),
        "status": fm.get("status", "needs-answers"),
        "created": fm.get("created", ""),
        "anchors": anchors,
        "roadmap": target.split(":", 1)[1] if target.startswith("roadmap:") else None,
        "summary": " ".join(sm.group(1).split()) if sm else "",
    }, ref

def find_config(start):
    d = os.path.dirname(os.path.abspath(start))
    while True:
        p = os.path.join(d, ".living-manual.json")
        if os.path.exists(p):
            return p
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent

def tracker_of(cfg):
    """-> (provider, provider config). Legacy top-level jira still reads."""
    t = cfg.get("tracker")
    if isinstance(t, dict):
        return t.get("provider", "none"), t
    legacy = cfg.get("jira")
    if isinstance(legacy, dict) and legacy.get("enabled"):
        return "jira", {"jira": legacy}
    return "none", {}

def issue_number(ref):
    """The trailing number of owner/name#42, #42, or 42."""
    m = re.search(r"#(\d+)\s*$", ref or "")
    if m:
        return m.group(1)
    s = (ref or "").strip()
    return s if s.isdigit() else None

def github_issues(conf):
    cmd = ["gh", "issue", "list", "--state", "open", "--limit", "200",
           "--json", "number,title,body,labels,url"]
    repo = (conf.get("github") or {}).get("repo")
    if repo:
        cmd += ["--repo", repo]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError((r.stderr.strip().splitlines() or ["gh issue list failed"])[0])
    return json.loads(r.stdout or "[]")

def type_from_labels(labels, mapping):
    have = {str(l).lower() for l in labels}
    for typ, lab in (mapping or {}).items():
        if isinstance(lab, str) and lab.lower() in have:
            return typ
    return "idea"

def status_from_body(body):
    # Ticket bodies the plugin wrote lead with "Status: <x>"; anything
    # else is an issue filed by hand, which has no local ticket yet.
    m = re.search(r"[Ss]tatus:\s*([a-z][a-z-]*)", (body or "")[:400])
    return m.group(1) if m and m.group(1) in STATUSES else "needs-answers"

def summary_from_body(body):
    m = re.search(r"^##\s+Summary\s*\n(.*?)(?=^##\s|\Z)", body or "", re.S | re.M)
    text = m.group(1) if m else (body or "")
    text = " ".join(text.split())
    return (text[:397].rstrip() + "...") if len(text) > 400 else text

def from_tracker(cfg, known_refs, warn):
    """Open tracker issues no local ticket file already references."""
    provider, tconf = tracker_of(cfg)
    if provider in ("none", None, ""):
        return []
    if provider == "jira":
        warn("tracker is jira: reconciliation needs the Atlassian MCP, so "
             "only a Claude Code session can do it. Run the ticket skill to "
             "check for Jira issues missing a local ticket.")
        return []
    if provider != "github":
        warn("unknown tracker provider %r: skipping reconciliation" % provider)
        return []
    try:
        issues = github_issues(tconf)
    except FileNotFoundError:
        warn("gh CLI not found: skipping tracker reconciliation")
        return []
    except subprocess.TimeoutExpired:
        warn("gh timed out: skipping tracker reconciliation")
        return []
    except Exception as e:
        warn("could not read GitHub issues (%s): skipping reconciliation" % e)
        return []
    labels_map = (tconf.get("github") or {}).get("labels")
    out = []
    for it in issues:
        num = str(it.get("number"))
        if num in known_refs:
            continue
        body = it.get("body") or ""
        out.append({
            "id": "#" + num,
            "title": it.get("title", "(untitled)"),
            "type": type_from_labels(
                [l.get("name", "") for l in it.get("labels") or []], labels_map),
            "status": status_from_body(body),
            "created": "",
            # An issue carries no manual anchor, so it can't match a
            # section; it surfaces under "everything queued" instead.
            "anchors": [],
            "roadmap": None,
            "summary": summary_from_body(body),
            "origin": "tracker",
            "url": it.get("url", ""),
        })
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    tdir, manual = args[0], args[1]

    tickets, refs = [], set()
    for name in sorted(os.listdir(tdir)):
        if re.match(r"TICKET-\d{4}.*\.md$", name):
            entry, ref = parse(os.path.join(tdir, name))
            if entry:
                tickets.append(entry)
            num = issue_number(ref)
            if num:
                refs.add(num)
            if ref:
                refs.add(ref.strip())

    warnings = []
    tracked = []
    if "--no-tracker" not in flags:
        cfg_path = find_config(manual)
        if cfg_path:
            try:
                cfg = json.load(open(cfg_path))
            except Exception as e:
                warnings.append("could not read %s (%s)" % (cfg_path, e))
                cfg = {}
            tracked = from_tracker(cfg, refs, warnings.append)
        else:
            warnings.append("no .living-manual.json found: skipping tracker reconciliation")

    si = load_sync(os.path.dirname(os.path.abspath(__file__)))
    src = open(manual).read()
    src = si.replace_block(src, "TICKETS",
                           "\n  var TICKETS = %s;\n  " % si.js(tickets + tracked))
    open(manual, "w").write(src)

    for w in warnings:
        print("warning:", w, file=sys.stderr)
    print("indexed %d queued ticket(s)" % len(tickets))
    if tracked:
        print("folded in %d open tracker issue(s) with no local ticket file:"
              % len(tracked))
        for t in tracked:
            print("  %s %s" % (t["id"], t["title"]))
        print("Write local tickets for these with the ticket skill; the file "
              "is the record.")

if __name__ == "__main__":
    main()
