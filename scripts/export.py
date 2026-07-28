#!/usr/bin/env python3
"""export.py MANUAL [DEST] — a static copy of the manual, for distribution.

The maintained manual is built for the people who maintain the code:
every heading files a note, the modal shows the internal queue, and the
payload is addressed to a Claude Code session. None of that survives
being handed to a wider audience, and some of it should not travel at
all: the queue data lives inside the file, so a distributed manual that
still carries the TICKETS block publishes the backlog and names the
issue tracker to anyone who views source.

What comes out:
  - no note-filing path, and no affordance advertising one
  - no TICKETS and no QUEUE_SYNC, in any form
  - no roadmap previews (they describe work that has not shipped)
  - the glossary intact, because it generates nothing and only makes
    the document easier to read
  - one manual-export comment naming the version and source commit,
    in place of the base marker and fingerprints, which are guard
    machinery this file is not maintained by

Removal is driven by /*@EXPORT-DROP*/ ... /*@/EXPORT-DROP*/ markers
(and their <!--@EXPORT-DROP--> form in markup), so the shell declares
which regions do not survive rather than this script guessing from
selectors that will drift.

Default destination is the manual's path with .html replaced by
_prod.html. The manual's own path is refused. Output is deterministic:
the same input produces byte-identical output.
"""
import json, os, re, subprocess, sys

DROP_PAIRS = [("/*@EXPORT-DROP*/", "/*@/EXPORT-DROP*/"),
              ("<!--@EXPORT-DROP-->", "<!--@/EXPORT-DROP-->")]
# Data blocks that must not travel. GLOSSARY and DEFINED stay: the
# glossary is a reading aid that generates nothing.
DROP_BLOCKS = ("TICKETS", "QUEUESYNC", "PREVIEWS")
# Declared for the note payload only; nothing that survives reads them.
DROP_VARS = ("MANUAL_VERSION", "MANUAL_BASE", "TICKET_SKILL",
             "TICKETS_DIR", "MANUAL_PATH")
EXPORT_MARK = "manual-export:"

def die(msg):
    sys.exit("export: " + msg)

def drop_marked(src):
    """Remove every marked region, in either comment syntax."""
    for open_m, close_m in DROP_PAIRS:
        while True:
            oi = src.find(open_m)
            if oi == -1:
                break
            ci = src.find(close_m, oi)
            if ci == -1:
                die("unclosed %s marker; the manual's shell is damaged" % open_m)
            # Take the whole lines, so no blank shell is left behind.
            ls = src.rfind("\n", 0, oi) + 1
            le = src.find("\n", ci + len(close_m))
            src = src[:ls] + src[le + 1:] if le != -1 else src[:ls]
    return src

def drop_block(src, name):
    """Remove a /*@NAME*/ ... /*@/NAME*/ data block and its var."""
    open_m, close_m = "/*@%s*/" % name, "/*@/%s*/" % name
    ci = src.rfind(close_m)
    if ci == -1:
        return src
    oi = src.rfind(open_m, 0, ci)
    if oi == -1:
        return src
    ls = src.rfind("\n", 0, oi) + 1
    le = src.find("\n", ci + len(close_m))
    return src[:ls] + src[le + 1:] if le != -1 else src[:ls]

def drop_preview_icons(src):
    """Remove the inline preview buttons and any orphaned data-preview.

    These are scattered through prose rather than living in one region,
    so they cannot be marked. Left behind they would be dead controls
    with no handler, which FR-3 exists to prevent.
    """
    src = re.sub(r'[ \t]*<button[^>]*class="preview-btn"[^>]*>.*?</button>',
                 "", src, flags=re.S)
    return re.sub(r'\s+data-preview="[^"]*"', "", src)

def source_commit(manual):
    repo = os.path.dirname(os.path.abspath(manual)) or "."
    r = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "unknown"

def plugin_version():
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(here, "..", ".claude-plugin", "plugin.json")) as f:
            return json.load(f).get("version", "unknown")
    except Exception:
        return "unknown"

def stamp_provenance(src, version, commit):
    """Swap the guard's markers for one provenance comment.

    That comment is also what tells verify.py which ruleset applies, so
    the file declares its own kind. A flag would have to be remembered
    by every later caller; the file outlives the command that made it.
    """
    src = re.sub(r"[ \t]*<!-- manual-fingerprint.*?-->\n?", "", src, flags=re.S)
    mark = "<!-- %s static copy, living-manual %s, built from %s -->" % (
        EXPORT_MARK, version, commit)
    src, n = re.subn(r"<!-- manual-base: [0-9a-f]+ -->", mark, src, count=1)
    if not n:
        die("no manual-base marker found; is this a living manual?")
    return src

def notice(src):
    """Tell the reader what this copy is, in place of the intro callout
    that explains affordances the export no longer has."""
    block = (
        '  <div class="callout manual-meta">\n'
        '    <p><b>This is a static copy.</b> It documents the release it was\n'
        '    built from and does not change. The note-filing, queue, and\n'
        '    roadmap-preview features of the maintained manual are not part of\n'
        '    it, so notes cannot be filed from this file.</p>\n'
        '  </div>')
    src, n = re.subn(r'[ \t]*<div class="callout tip manual-meta">.*?</div>',
                     lambda m: block, src, count=1, flags=re.S)
    if not n:
        # No intro callout to replace (a manual that never had one): put
        # the notice at the top of main so the statement is never absent.
        src = src.replace("<main>", "<main>\n" + block, 1)
    return src

def ensure_ignored(dest, manual):
    """Keep the export out of git.

    It is a build artifact: committing one would create a second
    document to keep current, and the point is that there is only ever
    one. Says nothing when git already ignores it, however that was
    arranged, so a repo with its own rule is not second-guessed.
    """
    repo = os.path.dirname(os.path.abspath(manual)) or "."
    top = subprocess.run(["git", "-C", repo, "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if top.returncode != 0:
        return
    root = top.stdout.strip()
    ignored = subprocess.run(["git", "-C", root, "check-ignore", "-q",
                              os.path.abspath(dest)], capture_output=True)
    if ignored.returncode == 0:
        return
    path = os.path.join(root, ".gitignore")
    rule = "*_prod.html"
    with open(path, "a") as fh:
        fh.write("\n# living-manual: static exports are build artifacts,\n"
                 "# regenerated at release rather than committed.\n%s\n" % rule)
    print("note: added %s to .gitignore (the export is a build artifact)" % rule)

def main():
    if len(sys.argv) < 2:
        die("usage: export.py MANUAL [DEST]")
    manual = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else re.sub(
        r"\.html$", "", manual) + "_prod.html"
    if os.path.abspath(dest) == os.path.abspath(manual):
        die("destination is the manual itself; the export would overwrite "
            "the file it is made from")
    try:
        src = open(manual).read()
    except OSError as e:
        die("cannot read %s (%s)" % (manual, e))
    if EXPORT_MARK in src[:4000]:
        die("%s is already an export; export from the maintained manual"
            % manual)

    src = drop_marked(src)
    for name in DROP_BLOCKS:
        src = drop_block(src, name)
    src = drop_preview_icons(src)
    for v in DROP_VARS:
        src = re.sub(r'[ \t]*var %s = [^\n]*\n' % v, "", src)
    src = notice(src)
    src = stamp_provenance(src, plugin_version(), source_commit(manual))

    open(dest, "w").write(src)
    ensure_ignored(dest, manual)
    print("exported:", dest)
    print("  removed: note filing, queue, roadmap previews")
    print("  kept:    glossary, navigation, all prose")
    print("Static copy. Regenerate it rather than editing it.")

if __name__ == "__main__":
    main()
