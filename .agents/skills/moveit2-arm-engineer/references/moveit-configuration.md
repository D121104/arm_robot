# MoveIt configuration checks

- SRDF groups have valid chains/joints and named states.
- End-effector parent link and group are correct.
- Disabled collision pairs have a reason.
- Kinematics solver is installed, loaded and aligned with base/tip frames.
- MoveIt limits may narrow but should not silently expand URDF limits.
- Controller name, action namespace and joints match the running controller.
