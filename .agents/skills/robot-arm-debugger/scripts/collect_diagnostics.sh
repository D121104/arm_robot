#!/usr/bin/env bash
set -u
timeout_cmd=""; command -v timeout >/dev/null 2>&1 && timeout_cmd="timeout 8"
section() { printf '\n===== %s =====\n' "$1"; }
section "Timestamp and environment"
date --iso-8601=seconds 2>/dev/null || date
printf 'PWD=%s\nROS_DISTRO=%s\nROS_DOMAIN_ID=%s\nRMW_IMPLEMENTATION=%s\n' \
  "$PWD" "${ROS_DISTRO:-<unset>}" "${ROS_DOMAIN_ID:-<unset>}" "${RMW_IMPLEMENTATION:-<unset>}"
section "Repository files"
find . -type f \( -name 'package.xml' -o -name '*.urdf' -o -name '*.xacro' -o \
  -name '*.srdf' -o -name '*controller*.yaml' -o -name 'kinematics.yaml' -o \
  -name 'joint_limits.yaml' -o -name '*.launch.py' \) \
  -not -path './build/*' -not -path './install/*' -not -path './log/*' | sort | head -n 400
if ! command -v ros2 >/dev/null 2>&1; then section "Runtime"; echo "ros2 CLI unavailable."; exit 0; fi
section "Nodes"; $timeout_cmd ros2 node list 2>&1 || true
section "Topics"; $timeout_cmd ros2 topic list -t 2>&1 || true
section "Actions"; $timeout_cmd ros2 action list -t 2>&1 || true
section "Controllers"; $timeout_cmd ros2 control list_controllers 2>&1 || true
section "Hardware components"; $timeout_cmd ros2 control list_hardware_components 2>&1 || true
section "Hardware interfaces"; $timeout_cmd ros2 control list_hardware_interfaces 2>&1 || true
section "Joint states"; $timeout_cmd ros2 topic info /joint_states -v 2>&1 || true
section "Clock"; $timeout_cmd ros2 topic info /clock -v 2>&1 || true
