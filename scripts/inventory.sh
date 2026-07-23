#!/bin/sh
# inventory.sh [repo-root] — compact codebase orientation for the setup
# flow: framework, structure, UI surface candidates, recent history.
# Output is intentionally terse; the skill reads only what it needs.
cd "${1:-.}" || exit 1

echo "== framework signals =="
for f in package.json Cargo.toml pyproject.toml go.mod Gemfile pom.xml \
         src-tauri/tauri.conf.json app/src-tauri/tauri.conf.json; do
  [ -f "$f" ] && echo "$f"
done
[ -f package.json ] && python3 -c "
import json; p = json.load(open('package.json'))
deps = {**p.get('dependencies',{}), **p.get('devDependencies',{})}
known = [k for k in ('react','vue','svelte','next','@tauri-apps/api','electron','express','fastify') if k in deps]
print('deps:', ', '.join(known) or '(none recognized)')"

echo "== tree (src-ish, 3 levels) =="
find . -maxdepth 3 -type d \
  \( -name node_modules -o -name .git -o -name target -o -name dist -o -name build -o -name .next \) -prune \
  -o -type d -print 2>/dev/null | grep -Ei 'src|app|lib|pages|components|surfaces|views|routes' | head -40

echo "== UI surface candidates =="
grep -rEl --include='*.tsx' --include='*.jsx' --include='*.vue' --include='*.svelte' \
  'export (default )?(function|const)' src app 2>/dev/null | head -40

echo "== docs =="
find . -maxdepth 2 \( -iname 'readme*' -o -iname 'changelog*' -o -iname 'roadmap*' -o -iname 'decisions*' \) \
  -not -path './node_modules/*' 2>/dev/null | head -10

echo "== brand candidates =="
find . -maxdepth 2 -type d \( -iname brand -o -iname 'design*' -o -iname assets -o -iname identity \) \
  -not -path './node_modules/*' 2>/dev/null | head -10

echo "== recent history =="
git log --oneline -15 2>/dev/null
