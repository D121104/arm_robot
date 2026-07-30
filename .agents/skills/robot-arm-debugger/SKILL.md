---
name: robot-arm-debugger
description: Performs cross-layer diagnosis of ROS 2 robot arms across environment sourcing, launch, TF, joint states, robot description, ros2_control, controllers, MoveIt planning, trajectory execution, Gazebo and task nodes. Use when the failing layer is unclear, the arm plans but does not move, nodes hang, goals are rejected or aborted, or multiple configurations may disagree.
license: MIT
compatibility: ROS 2 Jazzy tools recommended; diagnostic collector is read-only and does not publish commands or change lifecycle/controller state.
metadata:
  version: "1.0.0"
  domain: "debugging"
---

# Robot Arm Debugger

## Strict rules

- Collect evidence before fixes.
- Do not repeatedly activate nodes/controllers without reading errors.
- Do not publish trajectories during initial diagnosis.
- Do not delete build artifacts as a first response.
- Separate symptoms, observations, hypotheses and verified causes.

## Diagnostic sequence

1. Environment and overlays.
2. Launch processes and nodes.
3. Parameters and namespaces.
4. TF and timestamps.
5. Joint-state source, freshness and names.
6. Hardware and controller states.
7. Actions/services.
8. MoveIt current state and scene.
9. Planning result and error code.
10. Controller selection, goal result and feedback.
11. Task-node executor/callback behavior.
12. Simulation clock, plugins and physics.

```bash
.agents/skills/robot-arm-debugger/scripts/collect_diagnostics.sh > /tmp/robot-arm-diagnostics.txt
```

Read [debug matrix](references/debug-matrix.md).

## Fix strategy

State the likely layer, cite evidence, propose one minimal fix, define a command
that confirms/falsifies it, and reassess if the result contradicts the hypothesis.
