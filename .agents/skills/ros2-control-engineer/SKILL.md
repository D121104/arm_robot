---
name: ros2-control-engineer
description: Configures and debugs ros2_control for robot arms, including hardware plugins, command/state interfaces, controller manager, joint_state_broadcaster, joint_trajectory_controller, gripper controllers, controller YAML, lifecycle and controller activation. Use when controllers are missing, inactive, fail to configure, reject trajectories, or do not match the URDF.
license: MIT
compatibility: ROS 2 Jazzy and ros2_control CLI expected for runtime inspection; bundled scripts perform read-only queries only.
metadata:
  version: "1.0.0"
  domain: "control"
---

# ros2_control Engineer

## Non-negotiable safety

- Do not activate physical hardware or controllers without explicit approval.
- Do not switch controllers, publish commands or send trajectories during diagnosis.
- Never bypass hardware limits or fake feedback.
- Prefer simulation or mock hardware for first execution tests.

## Diagnostic order

1. Verify `<ros2_control>` plugin, parameters and joints.
2. Compare exported command/state interfaces with controller requirements.
3. Verify YAML loads into the correct controller manager namespace.
4. Inspect hardware component state.
5. Inspect controller state and claimed interfaces.
6. Verify joint-state names and timestamps.
7. Verify trajectory action names and joint order.
8. Compare MoveIt controller mapping.
9. Propose activation/switching commands only after diagnosis and for user review.

```bash
.agents/skills/ros2-control-engineer/scripts/inspect_control.sh
```

Read [controller configuration](references/controller-configuration.md) and
[hardware interfaces](references/hardware-interfaces.md).

## Key invariants

Controller joints exist in URDF, required interfaces are available, command
interfaces are not conflicting, joint states update, and MoveIt maps to the real
action namespace.
