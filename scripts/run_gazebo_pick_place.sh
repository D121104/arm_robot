#!/usr/bin/env bash
# Launch the five-object Panda Gazebo pick-and-place simulation in a new terminal.
# Usage:
#   ./scripts/run_gazebo_pick_place.sh
#   ./scripts/run_gazebo_pick_place.sh --headless --seed 42
#   ./scripts/run_gazebo_pick_place.sh --no-build

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ROS_SETUP="/opt/ros/jazzy/setup.bash"
HEADLESS=false
BUILD_WORKSPACE=true
RANDOM_SEED=""

usage() {
  cat <<'EOF'
Usage: run_gazebo_pick_place.sh [OPTIONS]

Build and launch the Panda five-object physical-contact pick-and-place demo
in a new GNOME Terminal window.

Options:
  --headless       Run Gazebo server without Gazebo GUI or RViz.
  --seed NUMBER    Use a reproducible random pick order.
  --no-build       Skip colcon build and use the existing install overlay.
  -h, --help       Show this help message.
EOF
}

while (($# > 0)); do
  case "$1" in
    --headless)
      HEADLESS=true
      ;;
    --seed)
      if (($# < 2)) || [[ ! "$2" =~ ^-?[0-9]+$ ]]; then
        echo "--seed requires an integer value." >&2
        exit 2
      fi
      RANDOM_SEED="$2"
      shift
      ;;
    --no-build)
      BUILD_WORKSPACE=false
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ ! -f "$ROS_SETUP" ]]; then
  echo "ROS 2 Jazzy setup file was not found: $ROS_SETUP" >&2
  exit 1
fi

if ! command -v gnome-terminal >/dev/null 2>&1; then
  echo "gnome-terminal is required to create a new terminal window." >&2
  exit 1
fi

LAUNCH_ARGS=(
  "backend:=gazebo"
)

if "$HEADLESS"; then
  LAUNCH_ARGS+=("headless:=true" "start_rviz:=false")
fi

if [[ -n "$RANDOM_SEED" ]]; then
  LAUNCH_ARGS+=("--ros-args" "-p" "random_seed:=${RANDOM_SEED}")
fi

COMMAND=(
  "cd $(printf '%q' "$WORKSPACE_DIR")"
  "&&"
  "source $(printf '%q' "$ROS_SETUP")"
)

if "$BUILD_WORKSPACE"; then
  COMMAND+=(
    "&&"
    "colcon build --symlink-install --packages-select my_robot_arm_description my_robot_arm_control my_robot_arm_gazebo my_robot_arm_pick_place"
  )
fi

COMMAND+=(
  "&&"
  "source install/setup.bash"
  "&&"
  "ros2 launch my_robot_arm_pick_place pick_place.launch.py"
)

for argument in "${LAUNCH_ARGS[@]}"; do
  COMMAND+=("$(printf '%q' "$argument")")
done

COMMAND+=(
  ";"
  "status=\$?"
  ";"
  "echo"
  "echo \"Launch process exited with status \$status. Press Enter to close this terminal.\""
  ";"
  "read -r"
  ";"
  "exit \$status"
)

exec gnome-terminal --title="Panda 5-Object Pick-and-Place" -- bash -lc "${COMMAND[*]}"
