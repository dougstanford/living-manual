#!/usr/bin/env python3
"""verify.py MANUAL — static integrity checks for a living manual.

Checks: base marker present and resolving to a commit in the containing
repo, data markers intact, script parses (when node is available), no
duplicate element ids, every preview icon names a PREVIEWS entry,
PREVIEWS/TICKETS/DEFINED_IN blocks well-formed, every DEFINED_IN key
has a glossary entry. Exit 0 clean; exit 1 with findings.
"""
import json, os, re, shutil, subprocess, sys, tempfile

REQUIRED_TICKET_KEYS = ("id", "title", "type", "status", "summary")

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

    base = re.search(r"manual-base: ([0-9a-f]{6,})", src[:4000])
    if not base:
        f.append("no manual-base marker in the first 4000 bytes")
    elif shutil.which("git"):
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

    ids = re.findall(r'\bid="([^"]+)"', src)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        f.append("duplicate element ids: %s" % ", ".join(dupes))

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
