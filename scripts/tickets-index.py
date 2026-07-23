#!/usr/bin/env python3
"""tickets-index.py TICKETS_DIR MANUAL

Rebuilds the manual's TICKETS block from the ticket files themselves
(frontmatter + Summary section), so the queue index can never drift
from the directory. Tickets with status shipped or declined stay on
disk as the record and drop out of the index.
"""
import importlib.util, os, re, sys

def load_sync(scripts_dir):
    spec = importlib.util.spec_from_file_location(
        "sync_index", os.path.join(scripts_dir, "sync-index.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def parse(path):
    text = open(path).read()
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    if fm.get("status") in ("shipped", "declined"):
        return None
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
    }

def main():
    tdir, manual = sys.argv[1], sys.argv[2]
    tickets = []
    for name in sorted(os.listdir(tdir)):
        if re.match(r"TICKET-\d{4}.*\.md$", name):
            t = parse(os.path.join(tdir, name))
            if t:
                tickets.append(t)
    si = load_sync(os.path.dirname(os.path.abspath(__file__)))
    src = open(manual).read()
    src = si.replace_block(src, "TICKETS", "\n  var TICKETS = %s;\n  " % si.js(tickets))
    open(manual, "w").write(src)
    print("indexed %d queued ticket(s)" % len(tickets))

if __name__ == "__main__":
    main()
