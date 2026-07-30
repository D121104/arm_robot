# Project layout guidance

## Typical dependency direction

```text
description → hardware/control → MoveIt config → task/application → bringup
                       ↘ simulation ↗
```

Avoid circular dependencies. A description package should not depend on MoveIt
or application packages. Bringup may depend on most runtime packages, but should
contain little business logic.

## Files to locate

- `package.xml`, `CMakeLists.txt`, `setup.py`, `setup.cfg`;
- `*.urdf`, `*.xacro`, `*.srdf`;
- `ros2_controllers.yaml`, `moveit_controllers.yaml`;
- `kinematics.yaml`, `joint_limits.yaml`, planning pipeline YAML;
- launch files and RViz configs;
- hardware plugin source and plugin XML;
- task nodes and tests.

## Build strategy

```bash
colcon build --symlink-install --packages-up-to <target-package>
colcon test --packages-select <changed-packages>
colcon test-result --verbose
```
