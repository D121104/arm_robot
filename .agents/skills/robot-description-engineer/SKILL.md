---
name: robot-description-engineer
description: Creates, reviews, and troubleshoots robot-arm URDF, Xacro, SRDF-adjacent naming, meshes, inertials, joint limits, transmissions, ros2_control tags, and TF frames. Use for broken robot models, missing links, invalid transforms, bad joint axes, unrealistic Gazebo physics, or mismatched joint and frame names.
license: MIT
compatibility: ROS 2 Jazzy with xacro and urdf tools recommended; validation scripts do not command robot motion.
metadata:
  version: "1.0.0"
  domain: "robot-description"
---

# Robot Description Engineer

Use this skill for the model and transform layer of a robot arm.

## Safety and scope

- Never widen joint limits without evidence.
- Do not hide self-collisions or remove collision geometry merely to make planning pass.
- Preserve frame and joint names unless migration is intentional and complete.
- Use simplified collision meshes and detailed visual meshes when appropriate.

## Required workflow

1. Locate the top-level Xacro/URDF and includes.
2. Expand Xacro with launch-equivalent arguments.
3. Validate XML and URDF structure.
4. Build a joint/link/frame inventory.
5. Verify parent-child chains, joint origin, axis and limits.
6. Verify inertials for simulated links.
7. Compare joint names with `ros2_control`, SRDF, controller YAML and MoveIt.
8. Verify TF at runtime when possible.
9. Make the smallest consistent change.

## Safe validation

```bash
.agents/skills/robot-description-engineer/scripts/validate_description.sh
.agents/skills/robot-description-engineer/scripts/validate_description.sh path/to/robot.urdf.xacro
```

Read [URDF/Xacro checks](references/urdf-xacro-checks.md) and
[TF and inertial guidance](references/tf-and-inertials.md).

## Output requirements

Report file and element, current value, violated invariant, patch, and static plus
runtime validation commands.
