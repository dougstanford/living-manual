#!/usr/bin/env python3
"""sync-index.py MANUAL PAYLOAD.json

Rewrites the manual's data blocks from a JSON payload so Claude edits
structured data, never raw HTML. The template wraps each block in
markers: /*@NAME*/ ... /*@/NAME*/.

Payload keys (all optional; present keys replace the whole block):
  tickets   -> var TICKETS = [...];
  previews  -> var PREVIEWS = {...};
  glossary  -> var GLOSSARY = [...];   (entries: id, label, pattern, flags,
               summary; "s" accepted as a legacy alias for summary)
  defined   -> var DEFINED_IN = {...};
  asof      -> the hero "as of" date string
  base      -> the manual-base commit sha (short); stamped into both the
               HTML comment and the MANUAL_BASE payload variable so a note's
               ticket names the commit the manual reflected

Stamping the base also records a content fingerprint: one git hash per
user_facing_paths entry, taken at the stamped commit. The sha alone is
fragile, because it is frozen in a file while history is not: an amend,
a rebase, or a squash merge orphans it, and with the commit gone there
is no range left to diff, so the update flow cannot say what changed.
The fingerprints answer that question without the commit. Identical
hashes mean nothing user-facing moved and only the marker needs
re-stamping; a differing hash names the surface that moved.

Glossary regexes travel as {"pattern": "...", "flags": "gi"} and are
emitted as literals.
"""
import json, os, re, subprocess, sys

def js(v):
    return json.dumps(v, ensure_ascii=False, indent=2)

def glossary_js(entries):
    out = []
    for e in entries:
        # A bare / inside a pattern would end the JS regex literal early.
        pattern = re.sub(r"(?<!\\)/", r"\\/", e["pattern"])
        summary = e.get("summary", e.get("s"))
        if summary is None:
            sys.exit("glossary entry %s has no summary" % e.get("id", "?"))
        out.append(
            "    { id: %s, label: %s, re: /%s/%s,\n      s: %s }"
            % (json.dumps(e["id"]), json.dumps(e["label"]),
               pattern, e.get("flags", "gi"), json.dumps(summary, ensure_ascii=False)))
    return "[\n" + ",\n".join(out) + "\n  ]"

FP_OPEN = "<!-- manual-fingerprint"

def find_config(start):
    """Nearest .living-manual.json at or above the manual."""
    d = os.path.dirname(os.path.abspath(start))
    while True:
        p = os.path.join(d, ".living-manual.json")
        if os.path.exists(p):
            return p
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent

def tree_hashes(base, paths, warn):
    """-> [(git hash, path)] for each path that resolves at `base`.

    A directory yields its tree hash, a file its blob hash; either way the
    hash changes exactly when that path's content does. An entry that is
    not a tracked path at all (a glob, a directory that exists only
    untracked) is skipped with a warning rather than failing the stamp:
    a config naming an as-yet-empty directory should keep working, and
    the remaining entries still fingerprint fine.
    """
    out = []
    for p in paths:
        spec = "%s:%s" % (base, p.rstrip("/"))
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet", spec],
                           capture_output=True, text=True)
        got = r.stdout.strip()
        # A zero exit is not enough. Handed something it cannot parse as a
        # rev -- a glob, say -- rev-parse can echo the argument straight
        # back and still succeed, which would stamp that string in place
        # of a hash. Only a 40-char sha is a fingerprint.
        if r.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", got):
            warn("user_facing_paths entry %r is not a tracked path at %s: "
                 "skipping its fingerprint" % (p, base))
            continue
        out.append((got, p))
    return out

def stamp_fingerprints(src, entries):
    """Write the fingerprint comment, replacing any previous one.

    It sits directly under the base marker because that is the region
    stale.sh and verify.py already read; keeping both in the first few
    hundred bytes means neither has to parse the whole document to
    answer a question about staleness.
    """
    body = (FP_OPEN + " (content hash per user-facing path, at that commit)\n"
            + "".join("     %s %s\n" % (h, p) for h, p in entries) + "-->")
    old = re.search(re.escape(FP_OPEN) + r".*?-->", src, re.S)
    if old:
        return src[:old.start()] + body + src[old.end():]
    anchor = re.search(r"<!-- manual-base: [0-9a-f]+ -->", src)
    if not anchor:
        # No marker to anchor to. verify.py reports that on its own; do
        # not invent a placement.
        return src
    return src[:anchor.end()] + "\n" + body + src[anchor.end():]

def replace_block(src, name, body):
    # Anchor on the LAST opening marker before the (unique) closing
    # marker. The token can appear earlier in prose — a maintenance
    # comment describing this mechanism — and a naive .*? from the first
    # occurrence would swallow the whole document between it and the real
    # closing marker. rindex is immune: the closing form "/*@/NAME*/"
    # never contains the opening form "/*@NAME*/" as a substring.
    open_m, close_m = f"/*@{name}*/", f"/*@/{name}*/"
    ci = src.rfind(close_m)
    if ci == -1:
        sys.exit(f"closing marker /*@/{name}*/ not found")
    oi = src.rfind(open_m, 0, ci)
    if oi == -1:
        sys.exit(f"opening marker /*@{name}*/ not found before its close")
    return src[:oi + len(open_m)] + body + src[ci:]

def main():
    manual, payload_path = sys.argv[1], sys.argv[2]
    src = open(manual).read()
    p = json.load(open(payload_path))
    if "tickets" in p:
        for t in p["tickets"]:
            missing = [k for k in ("id", "title", "type", "status", "summary") if k not in t]
            if missing:
                sys.exit("ticket %s missing keys: %s" % (t.get("id", "?"), ", ".join(missing)))
        src = replace_block(src, "TICKETS", "\n  var TICKETS = %s;\n  " % js(p["tickets"]))
    if "previews" in p:
        src = replace_block(src, "PREVIEWS", "\n  var PREVIEWS = %s;\n  " % js(p["previews"]))
    if "glossary" in p:
        src = replace_block(src, "GLOSSARY", "\n  var GLOSSARY = %s;\n  " % glossary_js(p["glossary"]))
    if "defined" in p:
        src = replace_block(src, "DEFINED", "\n  var DEFINED_IN = %s;\n  " % js(p["defined"]))
    if "asof" in p:
        # Lambda replacements: the value is inserted verbatim, never
        # re-interpreted for backslash escapes.
        src = re.sub(r'(<span id="asof-date">)[^<]*(</span>)',
                     lambda m: m.group(1) + p["asof"] + m.group(2), src, count=1)
        src = re.sub(r'(MANUAL_VERSION = ")[^"]*(")',
                     lambda m: m.group(1) + p["asof"] + m.group(2), src, count=1)
    warnings = []
    if "base" in p:
        src = re.sub(r"(manual-base: )[0-9a-f]+",
                     lambda m: m.group(1) + p["base"], src, count=1)
        src = re.sub(r'(MANUAL_BASE = ")[0-9a-f]+(")',
                     lambda m: m.group(1) + p["base"] + m.group(2), src, count=1)
        cfg_path = find_config(manual)
        cfg = {}
        if cfg_path:
            try:
                cfg = json.load(open(cfg_path))
            except Exception as e:
                warnings.append("could not read %s (%s): no fingerprints stamped"
                                % (cfg_path, e))
        else:
            warnings.append("no .living-manual.json found: no fingerprints stamped")
        paths = cfg.get("user_facing_paths") or []
        if paths:
            entries = tree_hashes(p["base"], paths, warnings.append)
            if entries:
                src = stamp_fingerprints(src, entries)
            else:
                warnings.append("no user_facing_paths entry resolved at %s: "
                                "no fingerprints stamped" % p["base"])
    open(manual, "w").write(src)
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    print("synced:", ", ".join(k for k in ("tickets","previews","glossary","defined","asof","base") if k in p))

if __name__ == "__main__":
    main()
