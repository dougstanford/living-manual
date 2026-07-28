#!/usr/bin/env python3
"""verify.py MANUAL — static integrity checks for a living manual.

Checks: base marker present and resolving to a commit in the containing
repo, the content fingerprints beside it well-formed when present, data
markers intact, script parses (when node is available), no duplicate
element ids, every preview icon names a PREVIEWS entry,
PREVIEWS/TICKETS/DEFINED_IN blocks well-formed, every DEFINED_IN key
has a glossary entry. Exit 0 clean; exit 1 with findings.
"""
import json, os, re, shutil, subprocess, sys, tempfile

REQUIRED_TICKET_KEYS = ("id", "title", "type", "status", "summary")

# How far into the file the marker region is expected to reach. The
# other readers open only this much rather than the whole manual, and
# the fingerprint comment grows with user_facing_paths, so there is
# headroom here for far more entries than a repo is likely to list.
MARKER_BYTES = 8000

def block(src, name):
    m = re.search(r"/\*@%s\*/(.*?)/\*@/%s\*/" % (name, name), src, re.S)
    return m.group(1) if m else None

def json_block(src, name, var):
    b = block(src, name)
    if b is None:
        return None, ["missing marker /*@%s*/" % name]
    m = re.search(r"var %s = (.*);" % var, b, re.S)
    if not m:
        return None, ["marker %s: no var %s" % (name, var)]
    try:
        return json.loads(m.group(1)), []
    except Exception as e:
        return None, ["marker %s: not valid JSON (%s)" % (name, e)]

def main():
    src = open(sys.argv[1]).read()
    f = []

    # A static export declares itself, so verification applies the rules
    # that fit what it is rather than faulting it for what was removed on
    # purpose. The file carries the declaration rather than the caller
    # passing a flag: the file outlives the command that made it, and a
    # copy verified a year from now should still be judged correctly.
    export = re.search(r"<!-- manual-export:[^>]*-->", src[:MARKER_BYTES])

    base = re.search(r"manual-base: ([0-9a-f]{6,})", src[:MARKER_BYTES])
    if not base and not export:
        f.append("no manual-base marker in the first %d bytes" % MARKER_BYTES)
    elif base and export:
        f.append("carries both a manual-export and a manual-base marker; an "
                 "export must not keep the guard's marker")
    elif base and shutil.which("git"):
        # The marker is a sha frozen in the file; amending or rebasing
        # after stamping orphans it and the guard breaks silently.
        repo_dir = os.path.dirname(os.path.abspath(sys.argv[1]))
        in_repo = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "--is-inside-work-tree"],
            capture_output=True)
        if in_repo.returncode == 0:
            r = subprocess.run(
                ["git", "-C", repo_dir, "cat-file", "-e",
                 base.group(1) + "^{commit}"], capture_output=True)
            if r.returncode != 0:
                f.append("manual-base %s does not resolve to a commit in "
                         "this repo (history rewritten after stamping?)"
                         % base.group(1))

    # The fingerprint comment is optional: a manual stamped before it
    # existed carries only a sha and is not faulted for it. But a
    # malformed one is worth a finding, because it is only ever read
    # after a rewrite has already orphaned the sha, and a garbled line
    # would fail exactly when it is the last thing left to recover from.
    fp = re.search(r"<!-- manual-fingerprint.*?-->", src[:MARKER_BYTES], re.S)
    if fp:
        lines = [l.strip() for l in fp.group(0).splitlines()[1:-1]]
        bad = [l for l in lines if l and not re.match(r"[0-9a-f]{40}\s+\S", l)]
        for l in bad:
            f.append("manual-fingerprint: unparseable entry %r "
                     "(want a 40-char hash, a space, then a path)" % l[:60])
        if not [l for l in lines if l]:
            f.append("manual-fingerprint block is present but empty")

    ids = re.findall(r'\bid="([^"]+)"', src)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        f.append("duplicate element ids: %s" % ", ".join(dupes))

    # Optional: manuals scaffolded before the queue stamp existed have
    # no such block, and that is not a fault. A present one must parse.
    if "/*@/QUEUESYNC*/" in src and not export:
        qsync, e = json_block(src, "QUEUESYNC", "QUEUE_SYNC"); f += e
        if qsync is not None and "provider" not in qsync:
            f.append("QUEUE_SYNC missing provider")

    # An export drops these three on purpose (queue data must not travel,
    # and previews describe work that has not shipped). Their absence is
    # the point, not a finding — but a damaged one still is.
    if export:
        previews = json_block(src, "PREVIEWS", "PREVIEWS")[0] if "/*@/PREVIEWS*/" in src else None
        tickets = json_block(src, "TICKETS", "TICKETS")[0] if "/*@/TICKETS*/" in src else None
        for name, present in (("TICKETS", tickets is not None),
                              ("PREVIEWS", previews is not None),
                              ("QUEUESYNC", "/*@/QUEUESYNC*/" in src)):
            if present:
                f.append("export still carries the %s block; it must not "
                         "travel with a distributed copy" % name)
    else:
        previews, e = json_block(src, "PREVIEWS", "PREVIEWS"); f += e
        tickets, e = json_block(src, "TICKETS", "TICKETS"); f += e
    defined, e = json_block(src, "DEFINED", "DEFINED_IN"); f += e
    gb = block(src, "GLOSSARY")
    if gb is None:
        f.append("missing marker /*@GLOSSARY*/")
    gloss_ids = set(re.findall(r'id:\s*"([^"]+)"', gb or ""))

    for pid in re.findall(r'data-preview="([^"]+)"', src):
        if previews is not None and pid not in previews:
            f.append("preview icon references unknown entry: %s" % pid)
    if previews:
        for k, v in previews.items():
            for key in ("title", "status", "source", "body"):
                if key not in v:
                    f.append("preview %s missing %s" % (k, key))

    if tickets is not None:
        for t in tickets:
            missing = [k for k in REQUIRED_TICKET_KEYS if k not in t]
            if missing:
                f.append("ticket %s missing: %s" % (t.get("id", "?"), ", ".join(missing)))

    if defined is not None:
        for k, ctxs in defined.items():
            if gloss_ids and k not in gloss_ids:
                f.append("DEFINED_IN key %s has no glossary entry" % k)
            if not isinstance(ctxs, list):
                # A bare string would iterate per character below and
                # bury the real mistake under nonsense findings.
                f.append("DEFINED_IN %s: value must be a list of contexts, "
                         "got %s" % (k, type(ctxs).__name__))
                continue
            for c in ctxs:
                if not (c.startswith("sec:") or c.startswith("h3:")):
                    f.append("DEFINED_IN %s: bad context %s" % (k, c))

    m = re.search(r"<script>(.*)</script>", src, re.S)
    if not m:
        f.append("no script block")
    elif shutil.which("node"):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t:
            t.write(m.group(1))
            tmp = t.name
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            first = (r.stderr.strip().splitlines() or ["unknown error"])[0]
            f.append("script does not parse: " + first)

    if f:
        print("FINDINGS:")
        for x in f:
            print(" -", x)
        sys.exit(1)
    print("OK")

if __name__ == "__main__":
    main()
