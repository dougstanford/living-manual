#!/usr/bin/env python3
"""tickets-index.py TICKETS_DIR MANUAL [--no-tracker] [--check]

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

Writing also records when the reconciliation happened and which
provider answered, because the block it writes is a snapshot: the
manual is self-contained and makes no network call when opened, so a
reader sees whatever was true at the last rebuild. The modal shows that
timestamp beside the queue, so a stale queue at least says how stale.

`--check` compares instead of writing, for the pre-push guard and CI.
Its exit contract is documented on do_check.
"""
import importlib.util, json, os, re, subprocess, sys, time

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
    """Which note type an issue's labels say it is.

    A type maps to one label or to a list of them. Any one of a type's
    labels identifies it: an issue routed as bug + needs-triage is still
    a bug when someone drops the routing label. First match wins, so a
    label named under two types resolves to whichever is declared first.
    """
    have = {str(l).lower() for l in labels}
    for typ, lab in (mapping or {}).items():
        names = [lab] if isinstance(lab, str) else (lab or [])
        if any(isinstance(n, str) and n.lower() in have for n in names):
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
    """-> (open issues with no local ticket file, provider actually read).

    The second value is the provider name only when its issue list came
    back, and None otherwise. Without it an empty list is ambiguous: a
    tracker with nothing open and a tracker that could not be reached
    look identical, and the drift check would report someone else's
    outage as a queue that had lost every issue.
    """
    provider, tconf = tracker_of(cfg)
    if provider in ("none", None, ""):
        return [], None
    if provider == "jira":
        warn("tracker is jira: reconciliation needs the Atlassian MCP, so "
             "only a Claude Code session can do it. Run the ticket skill to "
             "check for Jira issues missing a local ticket.")
        return [], None
    if provider != "github":
        warn("unknown tracker provider %r: skipping reconciliation" % provider)
        return [], None
    try:
        issues = github_issues(tconf)
    except FileNotFoundError:
        warn("gh CLI not found: skipping tracker reconciliation")
        return [], None
    except subprocess.TimeoutExpired:
        warn("gh timed out: skipping tracker reconciliation")
        return [], None
    except Exception as e:
        warn("could not read GitHub issues (%s): skipping reconciliation" % e)
        return [], None
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
    return out, provider

def published_tickets(src):
    """The TICKETS array already in the manual, or None if unreadable.

    Anchored like sync-index.replace_block: last opening marker before
    the closing one, because the token appears in prose too.
    """
    ci = src.rfind("/*@/TICKETS*/")
    if ci == -1:
        return None
    oi = src.rfind("/*@TICKETS*/", 0, ci)
    if oi == -1:
        return None
    m = re.search(r"var TICKETS = (.*);", src[oi:ci], re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def stamp_queue_sync(si, src, at, provider):
    """Record when the queue was last reconciled, and against what.

    A manual scaffolded before this block existed simply does not get
    one; the modal treats a missing stamp as an unknown age rather than
    a fresh one, so nothing needs backfilling.
    """
    if "/*@/QUEUESYNC*/" not in src:
        return src, False
    body = "\n  var QUEUE_SYNC = %s;\n  " % si.js({"at": at, "provider": provider})
    return si.replace_block(src, "QUEUESYNC", body), True

def load_tickets(tdir):
    """-> (index entries, every tracker ref the files mention)."""
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
    return tickets, refs

def read_config(manual, warn):
    cfg_path = find_config(manual)
    if not cfg_path:
        warn("no .living-manual.json found: skipping tracker reconciliation")
        return {}
    try:
        return json.load(open(cfg_path))
    except Exception as e:
        warn("could not read %s (%s)" % (cfg_path, e))
        return {}

def do_check(tdir, manual):
    """FR of the drift check: compare, never write. -> exit code.

    Exit contract, relied on by the pre-push guard and by CI:
      0  the manual's queue agrees with the tracker, OR the comparison
         could not be made (no tracker, unreachable, unreadable block)
      1  they disagree

    Everything unprovable exits zero on purpose. A queue that is merely
    out of date leaves the guard working and fixes itself on the next
    rebuild, and proving drift needs a third party that can be down for
    reasons the pusher did not cause. Failing a push on that would teach
    people to reach for --no-verify, which costs more than this check is
    worth.
    """
    notes = []
    tickets, refs = load_tickets(tdir)
    cfg = read_config(manual, notes.append)
    live, reached = from_tracker(cfg, refs, notes.append)
    for n in notes:
        print("note:", n)
    if not reached:
        print("queue check: no tracker was read, so there is nothing to "
              "compare. Not drift.")
        return 0

    try:
        published = published_tickets(open(manual).read())
    except OSError as e:
        print("queue check: could not open %s (%s). Not drift." % (manual, e))
        return 0
    if published is None:
        print("queue check: could not read the TICKETS block in %s. Not "
              "drift; verify.py reports a malformed manual." % manual)
        return 0

    # Only tracker-sourced entries can drift. The rest are built from the
    # ticket files, and the directory is the record: it cannot disagree
    # with itself between rebuilds.
    have = {t.get("id"): t for t in published if t.get("origin") == "tracker"}
    want = {t.get("id"): t for t in live}
    diffs = []
    for k in sorted(want.keys() - have.keys()):
        diffs.append(("added", k, want[k]["title"]))
    for k in sorted(have.keys() - want.keys()):
        diffs.append(("removed", k, have[k].get("title", "")))
    for k in sorted(want.keys() & have.keys()):
        for field in ("title", "status"):
            a, b = have[k].get(field, ""), want[k].get(field, "")
            if a != b:
                diffs.append(("changed", k, "%s: %r -> %r" % (field, a, b)))

    if not diffs:
        print("queue check: the manual's queue matches %s." % reached)
        return 0
    print("queue drift: %d difference(s) between the manual's queue and %s"
          % (len(diffs), reached))
    for kind, ref, detail in diffs:
        print("  %-8s %-6s %s" % (kind, ref, detail))
    print("Rebuild the queue:  python3 %s %s %s"
          % (os.path.abspath(__file__), tdir, manual))
    return 1

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    tdir, manual = args[0], args[1]

    if "--check" in flags:
        sys.exit(do_check(tdir, manual))

    tickets, refs = load_tickets(tdir)

    warnings = []
    tracked, reached = [], None
    if "--no-tracker" not in flags:
        cfg = read_config(manual, warnings.append)
        tracked, reached = from_tracker(cfg, refs, warnings.append)

    si = load_sync(os.path.dirname(os.path.abspath(__file__)))
    src = open(manual).read()
    src = si.replace_block(src, "TICKETS",
                           "\n  var TICKETS = %s;\n  " % si.js(tickets + tracked))
    stamped_at = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    src, stamped = stamp_queue_sync(si, src, stamped_at, reached or "none")
    open(manual, "w").write(src)

    for w in warnings:
        print("warning:", w, file=sys.stderr)
    print("indexed %d queued ticket(s)" % len(tickets))
    if stamped:
        print("reconciled %s against %s" % (stamped_at, reached or "no tracker"))
    if tracked:
        print("folded in %d open tracker issue(s) with no local ticket file:"
              % len(tracked))
        for t in tracked:
            print("  %s %s" % (t["id"], t["title"]))
        print("Write local tickets for these with the ticket skill; the file "
              "is the record.")

if __name__ == "__main__":
    main()
