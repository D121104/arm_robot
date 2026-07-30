---
name: robot-arm-workspace
description: Inspects and organizes ROS 2 robot-arm repositories and workspaces. Use when starting a robot arm project, reviewing package layout, planning architecture, identifying package boundaries, selecting build/test commands, or determining whether a problem belongs to description, control, planning, simulation, or application code.
license: MIT
compatibility: Designed for ROS 2 Jazzy workspaces on Ubuntu; commands are read-only unless the user explicitly asks for code changes.
metadata:
  version: "1.0.0"
  domain: "robotics"
---

# Robot Arm Workspace

Use this skill to establish project context before changing robot-arm code.

## Mandatory behavior

1. Inspect before editing.
2. Determine repository root, workspace root, ROS distro, build system and package graph.
3. Classify the task into one or more layers: description/TF, hardware/control,
   MoveIt planning/execution, simulation, task behavior, or cross-layer debugging.
4. Prefer the smallest package-specific build and test command.
5. Do not install packages, run `sudo`, delete build artifacts or start hardware without explicit approval.
6. Treat ROS 2 Jazzy as the expected environment, but verify rather than assume.

## First inspection

```bash
.agents/skills/robot-arm-workspace/scripts/inspect_workspace.sh
```

## Architecture rules

Prefer separate packages for description, bringup, hardware, MoveIt config,
interfaces, manipulation tasks and simulation. Do not split packages mechanically;
follow existing repository conventions unless a change has a clear benefit.

## Workflow

1. Inventory packages and files.
2. Identify entry-point launch files.
3. Trace data flow from description to joint states, controllers, MoveIt and tasks.
4. Identify the narrowest failing layer.
5. Read the matching specialist skill.
6. Propose changes with exact files and verification commands.
7. Build only affected packages first.
8. Report verified facts separately from assumptions.

See [project layout guidance](references/project-layout.md) and the
[acceptance checklist](references/acceptance-checklist.md).

## Response format

Return detected environment, package/file map, likely layer and evidence,
minimal change, validation commands and remaining uncertainty.
