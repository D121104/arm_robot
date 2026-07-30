#!/usr/bin/env bash
set -u
timeout_cmd=""; command -v timeout >/dev/null 2>&1 && timeout_cmd="timeout 8"
echo "== MoveIt configuration files =="
find . -type f \( -name '*.srdf' -o -name 'kinematics.yaml' -o \
  -name 'joint_limits.yaml' -o -name '*moveit*controllers*.yaml' -o \
  -name '*planning*.yaml' -o -name '*.rviz' -o -name '*.launch.py' \) \
  -not -path './build/*' -not -path './install/*' -not -path './log/*' | sort | head -n 300
echo; echo "== Planning/controller markers =="
grep -RIn --exclude-dir=build --exclude-dir=install --exclude-dir=log \
  -E 'planning_group|move_group|MoveGroup|FollowJointTrajectory|kinematics_solver|planning_pipelines' . 2>/dev/null | head -n 300 || true
if ! command -v ros2 >/dev/null 2>&1; then echo "ros2 CLI unavailable; runtime skipped."; exit 0; fi
echo; echo "== Action servers =="; $timeout_cmd ros2 action list -t 2>&1 | grep -E 'move|trajectory|gripper|execute' || true
echo; echo "== MoveIt nodes =="; $timeout_cmd ros2 node list 2>&1 | grep -E 'move_group|planning|servo' || true
