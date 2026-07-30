#!/usr/bin/env bash
set -u
timeout_cmd=""; command -v timeout >/dev/null 2>&1 && timeout_cmd="timeout 8"
echo "== Configuration candidates =="
find . -type f \( -name '*controller*.yaml' -o -name '*.urdf' -o -name '*.xacro' \) \
  -not -path './build/*' -not -path './install/*' -not -path './log/*' | sort | head -n 250
echo; echo "== ros2_control markers =="
grep -RIn --exclude-dir=build --exclude-dir=install --exclude-dir=log \
  -E '<ros2_control|controller_manager|joint_trajectory_controller|joint_state_broadcaster' . 2>/dev/null | head -n 250 || true
if ! command -v ros2 >/dev/null 2>&1; then echo "ros2 CLI unavailable; runtime skipped."; exit 0; fi
echo; echo "== Controllers =="; $timeout_cmd ros2 control list_controllers 2>&1 || true
echo; echo "== Hardware components =="; $timeout_cmd ros2 control list_hardware_components 2>&1 || true
echo; echo "== Hardware interfaces =="; $timeout_cmd ros2 control list_hardware_interfaces 2>&1 || true
