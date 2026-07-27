#!/usr/bin/env python3
"""scaffold.py TEMPLATE CONFIG.json OUT.html

Instantiates the manual shell from brand config. Claude then fills the
content slots (<!-- SLOT: ... -->) with prose; everything mechanical is
already in place.

Config keys used (from .living-manual.json):
  product, tagline, tagline_pill, manual_path, tickets_dir,
  ticket_skill (payload command, default "/living-manual:ticket"),
  brand: { ink, surface, deep, accent, warn, caution,
           font_stack, hero_gradient_css, logo_data_uri }
Missing brand keys fall back to a neutral slate palette.

The scaffolded manual is fingerprinted at its base commit, the same way
an update run stamps it, so a brand new manual survives a history
rewrite. Setup is exactly when one is likely: the commits that introduce
a manual are the ones most often amended or squashed before they land.
"""
import importlib.util, json, os, re, subprocess, sys

DEFAULTS = {
    "ink": "#26282b", "surface": "#fafaf7", "deep": "#22303a",
    "accent": "#2545d3", "warn": "#c4553a", "caution": "#d8c95e",
    "font_stack": 'system-ui, "Segoe UI", sans-serif',
    "hero_gradient_css": "linear-gradient(135deg, #22303a 0%, #3a5266 100%)",
    "logo_data_uri": "",
}

def load_sync(scripts_dir):
    """sync-index.py owns the fingerprint format; import it rather than
    growing a second copy that can disagree about the marker."""
    spec = importlib.util.spec_from_file_location(
        "sync_index", os.path.join(scripts_dir, "sync-index.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    tpl_path, cfg_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    cfg = json.load(open(cfg_path))
    brand = {**DEFAULTS, **cfg.get("brand", {})}
    head = subprocess.run("git rev-parse --short HEAD", shell=True,
                          capture_output=True, text=True).stdout.strip() or "0000000"
    logo = ('<img src="%s" alt="" style="height:30px;width:auto;display:block">'
            % brand["logo_data_uri"]) if brand["logo_data_uri"] else ""
    subs = {
        "{{PRODUCT}}": cfg.get("product", "Product"),
        "{{TAGLINE}}": cfg.get("tagline", "The user's manual."),
        "{{TAGLINE_PILL}}": cfg.get("tagline_pill", ""),
        "{{TICKET_SKILL}}": cfg.get("ticket_skill", "/living-manual:ticket"),
        "{{TICKETS_DIR}}": cfg.get("tickets_dir", "docs/tickets"),
        "{{MANUAL_PATH}}": cfg.get("manual_path", "docs/USER_MANUAL.html"),
        "{{BASE_SHA}}": head,
        "{{INK}}": brand["ink"], "{{SURFACE}}": brand["surface"],
        "{{DEEP}}": brand["deep"], "{{ACCENT}}": brand["accent"],
        "{{WARN}}": brand["warn"], "{{CAUTION}}": brand["caution"],
        "{{FONT_STACK}}": brand["font_stack"],
        "{{HERO_GRADIENT}}": brand["hero_gradient_css"],
        "{{LOGO_TAG}}": logo,
    }
    src = open(tpl_path).read()
    for k, v in subs.items():
        src = src.replace(k, v)
    if not cfg.get("tagline_pill"):
        src = re.sub(r'\s*<span class="tagpill"></span>', "", src)
    warnings = []
    paths = cfg.get("user_facing_paths") or []
    if paths:
        si = load_sync(os.path.dirname(os.path.abspath(__file__)))
        entries = si.tree_hashes(head, paths, warnings.append)
        if entries:
            src = si.stamp_fingerprints(src, entries)
    open(out_path, "w").write(src)
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    print("scaffolded", out_path, "base", head)

if __name__ == "__main__":
    main()
