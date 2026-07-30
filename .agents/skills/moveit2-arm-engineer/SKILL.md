---
name: moveit2-arm-engineer
description: Builds and troubleshoots MoveIt 2 configurations for robot arms: SRDF planning groups, end effectors, kinematics, joint limits, planning pipelines, planning scene, controllers, MoveGroup interfaces, RViz planning and trajectory execution. Use when planning fails, execution fails, start state is invalid, collisions are unexpected, IK is unavailable, or MoveIt configuration files disagree.
license: MIT
compatibility: Intended for MoveIt 2 on ROS 2 Jazzy; runtime scripts only query files and ROS graph state.
metadata:
  version: "1.0.0"
  domain: "motion-planning"
---

# MoveIt 2 Arm Engineer

## Safety boundaries

- Separate planning from execution.
- Default to RViz or mock/simulated hardware.
- Never disable collision checking globally.
- Do not execute on physical hardware without explicit approval.
- Start with conservative velocity and acceleration scaling.

## Diagnostic workflow

1. Verify URDF/SRDF joints and frames.
2. Verify planning group and end effector.
3. Verify kinematics plugin and base/tip frames.
4. Verify current joint states reach the planning scene.
5. Verify start state limits and collisions.
6. Verify planning pipeline.
7. Verify controller mapping and action namespace.
8. Classify failure as state acquisition, planning, controller selection,
   action execution or feedback.
9. Validate in RViz before simulated or physical execution.

```bash
.agents/skills/moveit2-arm-engineer/scripts/inspect_moveit.sh
```

Read [configuration checks](references/moveit-configuration.md) and
[planning versus execution](references/planning-and-execution.md).

## Implementation policy

Match repository language and APIs, define group/frame names explicitly, check
plan results before execute, and return useful error information.
