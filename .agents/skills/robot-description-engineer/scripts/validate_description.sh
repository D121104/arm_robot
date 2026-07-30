#!/usr/bin/env bash
set -u
input="${1:-}"
if [[ -z "$input" ]]; then
  echo "Usage: $0 path/to/model.urdf[.xacro]"
  echo "Candidates:"
  find . -type f \( -name '*.urdf' -o -name '*.xacro' \) \
    -not -path './build/*' -not -path './install/*' -not -path './log/*' | sort
  exit 0
fi
[[ -f "$input" ]] || { echo "File not found: $input" >&2; exit 2; }
tmp="$(mktemp --suffix=.urdf)"; trap 'rm -f "$tmp"' EXIT
case "$input" in
  *.xacro) command -v xacro >/dev/null 2>&1 || { echo "xacro command is required" >&2; exit 3; }; xacro "$input" > "$tmp" || exit 4 ;;
  *) cp "$input" "$tmp" ;;
esac
if command -v check_urdf >/dev/null 2>&1; then check_urdf "$tmp" || exit 5; fi
python3 - "$tmp" <<'URDFPY'
import sys, xml.etree.ElementTree as ET
from collections import Counter
root=ET.parse(sys.argv[1]).getroot(); links=[e.get('name','') for e in root.findall('link')]
joints=root.findall('joint'); names=[e.get('name','') for e in joints]; errors=[]
for label, values in [('link',links),('joint',names)]:
    for name,count in Counter(values).items():
        if not name: errors.append(f'{label} missing name')
        elif count>1: errors.append(f'duplicate {label}: {name}')
link_set=set(links)
for j in joints:
    name=j.get('name','<unnamed>'); p=j.find('parent'); c=j.find('child')
    pv=p.get('link') if p is not None else None; cv=c.get('link') if c is not None else None
    if pv not in link_set: errors.append(f'{name}: missing parent link {pv}')
    if cv not in link_set: errors.append(f'{name}: missing child link {cv}')
    if j.get('type') in {'revolute','prismatic'}:
        limit=j.find('limit')
        if limit is None: errors.append(f'{name}: missing limit')
        else:
            for key in ('lower','upper','effort','velocity'):
                if limit.get(key) is None: errors.append(f'{name}: missing limit {key}')
print(f'links={len(links)} joints={len(joints)}')
if errors:
    print('\n'.join(f'- {e}' for e in errors)); raise SystemExit(1)
print('Basic XML/URDF consistency checks passed.')
URDFPY
