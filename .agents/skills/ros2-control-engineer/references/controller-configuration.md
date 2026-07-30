# Controller configuration

A common arm setup uses `joint_state_broadcaster`, an arm
`joint_trajectory_controller`, and a gripper action/position controller.

Confirm controller manager namespace and parameter path. For a trajectory
controller, check ordered joints, command/state interfaces, constraints,
tolerances and action namespace. Diagnose failed lifecycle transitions before
repeating activation commands.
