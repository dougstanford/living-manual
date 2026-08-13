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
  surfaces  -> truthy: re-stamp the manual-surfaces block, one content
               hash per user_facing_paths entry, taken at HEAD

The surfaces block is the whole staleness mechanism: a git hash per
user-facing path (a directory's tree hash, a file's blob hash), so a
hash changes exactly when that surface's content does. stale.sh answers
"is the manual current?" by comparing each path's hash at HEAD to the
one stored here — no commit sha, no commit range, no history walk. That
is what makes merges order-independent: a branch only rewrites the line
for a surface it actually changed, so two branches touching different
surfaces edit different lines and merge cleanly in any order, while two
branches touching the same surface collide on that one line, which is
the reconciliation a human owes anyway.

Stamp only after the prose is reconciled to HEAD: this marks those
surfaces "described", so stamping unreconciled code would lie.

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

SURF_OPEN = "<!-- manual-surfaces"

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

def tree_hashes(ref, paths, warn):
    """-> [(git hash, path)] for each path that resolves at `ref`.

    A directory yields its tree hash, a file its blob hash; either way the
    hash changes exactly when that path's content does. An entry that is
    not a tracked path at all (a glob, a directory that exists only
    untracked) is skipped with a warning rather than failing the stamp:
    a config naming an as-yet-empty directory should keep working, and
    the remaining entries still hash fine.
    """
    out = []
    for p in paths:
        spec = "%s:%s" % (ref, p.rstrip("/"))
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet", spec],
                           capture_output=True, text=True)
        got = r.stdout.strip()
        # A zero exit is not enough. Handed something it cannot parse as a
        # rev -- a glob, say -- rev-parse can echo the argument straight
        # back and still succeed, which would stamp that string in place
        # of a hash. Only a 40-char sha is a fingerprint.
        if r.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", got):
            warn("user_facing_paths entry %r is not a tracked path at %s: "
                 "skipping its surface hash" % (p, ref))
            continue
        out.append((got, p))
    return out

def stamp_surfaces(src, entries):
    """Write the manual-surfaces comment, replacing any previous one.

    It lives in the document head so stale.sh and verify.py read only the
    first few thousand bytes to answer a staleness question rather than
    parsing the whole file. A new manual ships the block already; on an
    update the existing block is replaced in place, which keeps unchanged
    lines byte-for-byte stable so a 3-way merge keeps whichever side moved.
    """
    # One blank line between entries is load-bearing, not cosmetic. Each
    # branch rewrites only the hash line for a surface it changed; a blank
    # line between two entries keeps those changes in separate merge hunks,
    # so git combines edits to different surfaces without a conflict.
    # Adjacent changed lines, with no unchanged line between them, would
    # conflict on every parallel merge — the very failure this replaced.
    body = (SURF_OPEN + " (content hash per user-facing path the manual reflects)\n\n"
            + "\n\n".join("     %s %s" % (h, p) for h, p in entries) + "\n-->")
    old = re.search(re.escape(SURF_OPEN) + r".*?-->", src, re.S)
    if old:
        return src[:old.start()] + body + src[old.end():]
    # No block yet. This may be a legacy manual carrying the old base-sha
    # markers; strip them so the migration is one clean swap rather than a
    # file that briefly holds both schemes.
    src = re.sub(r"[ \t]*<!-- manual-fingerprint.*?-->\n?", "", src, flags=re.S)
    src = re.sub(r"[ \t]*<!-- manual-base: [0-9a-f]+ -->\n?", "", src, count=1)
    # Anchor right after the <title>, the one stable line every manual head
    # carries. verify.py reports a truly place-less manual on its own; do
    # not invent a placement beyond this.
    anchor = re.search(r"</title>", src)
    if not anchor:
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
    if p.get("surfaces"):
        cfg_path = find_config(manual)
        cfg = {}
        if cfg_path:
            try:
                cfg = json.load(open(cfg_path))
            except Exception as e:
                warnings.append("could not read %s (%s): surfaces not stamped"
                                % (cfg_path, e))
        else:
            warnings.append("no .living-manual.json found: surfaces not stamped")
        paths = cfg.get("user_facing_paths") or []
        if paths:
            entries = tree_hashes("HEAD", paths, warnings.append)
            if entries:
                src = stamp_surfaces(src, entries)
            else:
                warnings.append("no user_facing_paths entry resolved at HEAD: "
                                "surfaces not stamped")
    open(manual, "w").write(src)
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    print("synced:", ", ".join(k for k in ("tickets","previews","glossary","defined","asof","surfaces") if k in p))

if __name__ == "__main__":
    main()
