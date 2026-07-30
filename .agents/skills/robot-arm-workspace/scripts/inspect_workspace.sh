#!/usr/bin/env bash
set -u
root="${1:-$PWD}"
cd "$root" 2>/dev/null || { echo "Cannot enter: $root" >&2; exit 2; }
printf '== Environment ==\n'
printf 'pwd=%s\n' "$PWD"
printf 'ROS_DISTRO=%s\n' "${ROS_DISTRO:-<unset>}"
printf 'AMENT_PREFIX_PATH=%s\n' "${AMENT_PREFIX_PATH:-<unset>}"
if command -v git >/dev/null 2>&1; then
  printf 'git_root=%s\n' "$(git rev-parse --show-toplevel 2>/dev/null || echo '<not a git repository>')"
fi
printf '\n== ROS packages ==\n'
if command -v colcon >/dev/null 2>&1; then colcon list 2>/dev/null || true
else find . -name package.xml -not -path './build/*' -not -path './install/*' -print; fi
printf '\n== Robot-arm files ==\n'
find . -type f \( -name '*.urdf' -o -name '*.xacro' -o -name '*.srdf' -o \
  -name '*controllers*.yaml' -o -name 'kinematics.yaml' -o \
  -name 'joint_limits.yaml' -o -name '*.launch.py' \) \
  -not -path './build/*' -not -path './install/*' -not -path './log/*' | sort | head -n 300
