---
name: robot-arm-task-builder
description: Implements safe robot-arm application behaviors such as joint-space moves, pose goals, gripper commands, pick-and-place, planning-scene objects, waypoint sequences and MoveIt Task Constructor workflows. Use when adding manipulation nodes, actions, services, state machines, retries, cancellation, task tests, or simulation demos after description, control and MoveIt are healthy.
license: MIT
compatibility: ROS 2 Jazzy and MoveIt 2; execution must remain simulation-first unless physical hardware is explicitly approved.
metadata:
  version: "1.0.0"
  domain: "manipulation-tasks"
---

# Robot Arm Task Builder

Use this skill only after description, control and MoveIt are healthy.

## Safety rules

- Build planning-only behavior first.
- Use validated targets and conservative scaling.
- Add collision objects before planning around them.
- Define TCP, grasp frame and approach/retreat directions explicitly.
- Implement cancellation and timeouts.
- Never run a task on real hardware without explicit approval.

## Design workflow

1. Define task inputs, outputs and failure states.
2. Choose function, service, action, state machine or MoveIt Task Constructor.
3. Reuse existing planning group, tool frame and controller integration.
4. Separate perception/object selection from motion planning when practical.
5. Add preconditions and scene validation.
6. Plan each stage and expose exact failures.
7. Retry only failures that are safe to retry.
8. Add tests not requiring physical hardware.

Typical pick-and-place stages:

```text
validate → add object → open → pre-grasp → approach → grasp → attach → lift →
transfer → lower → release → detach → retreat
```

Read [task architecture](references/task-architecture.md) and
[pick-and-place checks](references/pick-place-checklist.md).

## Implementation requirements

Match repository language; do not create a second executor inside an already
spinning callback; avoid blocking calls that can deadlock; parameterize groups,
frames, scaling and timeouts; return stage and error code on failure.
