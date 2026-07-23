#!/usr/bin/env python3
"""sync-index.py MANUAL PAYLOAD.json

Rewrites the manual's data blocks from a JSON payload so Claude edits
structured data, never raw HTML. The template wraps each block in
markers: /*@NAME*/ ... /*@/NAME*/.

Payload keys (all optional; present keys replace the whole block):
  tickets   -> var TICKETS = [...];
  previews  -> var PREVIEWS = {...};
  glossary  -> var GLOSSARY = [...];   (entries: id,label,pattern,flags,s)
  defined   -> var DEFINED_IN = {...};
  asof      -> the hero "as of" date string
  base      -> the manual-base commit sha (short)

Glossary regexes travel as {"pattern": "...", "flags": "gi"} and are
emitted as literals.
"""
import json, re, sys

def js(v):
    return json.dumps(v, ensure_ascii=False, indent=2)

def glossary_js(entries):
    out = []
    for e in entries:
        # A bare / inside a pattern would end the JS regex literal early.
        pattern = re.sub(r"(?<!\\)/", r"\\/", e["pattern"])
        out.append(
            "    { id: %s, label: %s, re: /%s/%s,\n      s: %s }"
            % (json.dumps(e["id"]), json.dumps(e["label"]),
               pattern, e.get("flags", "gi"), json.dumps(e["s"], ensure_ascii=False)))
    return "[\n" + ",\n".join(out) + "\n  ]"

def replace_block(src, name, body):
    pat = re.compile(r"(/\*@%s\*/)(.*?)(/\*@/%s\*/)" % (name, name), re.S)
    if not pat.search(src):
        sys.exit(f"marker /*@{name}*/ not found")
    return pat.sub(lambda m: m.group(1) + body + m.group(3), src, count=1)

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
    if "base" in p:
        src = re.sub(r"(manual-base: )[0-9a-f]+",
                     lambda m: m.group(1) + p["base"], src, count=1)
    open(manual, "w").write(src)
    print("synced:", ", ".join(k for k in ("tickets","previews","glossary","defined","asof","base") if k in p))

if __name__ == "__main__":
    main()
