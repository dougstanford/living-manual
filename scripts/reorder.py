#!/usr/bin/env python3
"""reorder.py MANUAL ID [ID ...] — apply a section order to the manual.

The manual's reorder mode lets a reader drag the top-level sections
into a new order and copy that order as a payload. This script is the
write-back half: it moves the <section> blocks in the file and the
matching TOC link groups, and touches nothing else. Prose, data
markers, and stamps are preserved byte for byte; only the order of
whole blocks changes. Output is deterministic.

Ids may be passed space- or comma-separated. The given set must equal
the manual's set of top-level section ids exactly; anything else is
refused with the difference named, because a silently dropped section
is a corrupted manual.

Exits 0 on success (also when the order is already in place), 1 on
refusal.
"""
import re, sys

def die(msg):
    sys.exit("reorder: " + msg)

def blocks_of(src, pattern, what):
    """Contiguous blocks matched by pattern, refusing non-whitespace gaps.

    Reordering works by rewriting the span from the first block to the
    last. Anything else inside that span would be silently glued to the
    end, so its existence is a refusal, not a guess.
    """
    found = list(re.finditer(pattern, src, re.S))
    if not found:
        die("no %s found" % what)
    for a, b in zip(found, found[1:]):
        gap = src[a.end():b.start()]
        if gap.strip():
            die("unexpected content between %s blocks (%r...); this layout "
                "is not safe to reorder mechanically" % (what, gap.strip()[:60]))
    return found

def main():
    if len(sys.argv) < 3:
        die("usage: reorder.py MANUAL ID [ID ...]")
    manual = sys.argv[1]
    order = []
    for arg in sys.argv[2:]:
        order.extend(p for p in re.split(r"[,\s]+", arg) if p)
    if len(order) != len(set(order)):
        die("duplicate ids in the requested order")
    src = open(manual).read()

    secs = blocks_of(src, r'[ \t]*<section id="([^"]+)">.*?</section>', "section")
    have = [m.group(1) for m in secs]
    if set(order) != set(have):
        missing = sorted(set(have) - set(order))
        unknown = sorted(set(order) - set(have))
        parts = []
        if missing:
            parts.append("missing from the request: " + ", ".join(missing))
        if unknown:
            parts.append("not in the manual: " + ", ".join(unknown))
        die("id sets differ (%s)" % "; ".join(parts))
    if order == have:
        print("already in that order; nothing to do")
        return

    by_id = {m.group(1): m.group(0) for m in secs}
    body = "\n\n".join(by_id[i] for i in order)
    src = src[:secs[0].start()] + body + src[secs[-1].end():]

    # TOC: a top-level link plus its following .sub links move as one
    # group. Links whose target is not a section (none today) would
    # break the contiguity check above and refuse cleanly.
    nav = re.search(r'<nav class="toc">.*?</nav>', src, re.S)
    if nav:
        links = blocks_of(nav.group(0),
                          r'[ \t]*<a [^>]*href="#([^"]+)"[^>]*>.*?</a>', "TOC link")
        groups, current = {}, None
        for m in links:
            if 'class="sub"' in m.group(0):
                if current:
                    groups[current].append(m)
                continue
            current = m.group(1)
            groups.setdefault(current, []).append(m)
        grouped = sum(len(v) for v in groups.values())
        if set(groups) == set(order) and grouped == len(links):
            nav_body = "\n".join("\n".join(l.group(0) for l in groups[i])
                                 for i in order)
            new_nav = (nav.group(0)[:links[0].start()] + nav_body
                       + nav.group(0)[links[-1].end():])
            src = src[:nav.start()] + new_nav + src[nav.end():]
        else:
            print("warning: TOC links do not map one-to-one onto sections; "
                  "TOC left untouched", file=sys.stderr)

    open(manual, "w").write(src)
    print("reordered %d sections: %s" % (len(order), " ".join(order)))

if __name__ == "__main__":
    main()
