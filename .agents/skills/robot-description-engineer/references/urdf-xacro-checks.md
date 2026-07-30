# URDF and Xacro checks

- One intended root link; unique link and joint names.
- Every joint parent and child exists; no accidental cycle.
- Revolute/prismatic limits include lower, upper, effort and velocity.
- Axis vectors and joint origins match the mechanical convention.
- Mesh paths resolve after installation; units are meters and radians.
- Collision geometry is appropriately simplified.
- Xacro switches for hardware/simulation are explicit.
- Test the exact macro entry point and arguments used by launch.
