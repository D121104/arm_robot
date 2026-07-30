# Robot arm debug matrix

| Symptom | First layer | Evidence |
|---|---|---|
| Broken model in RViz | description/TF | robot_description, Xacro, TF |
| Joint states absent | control/hardware | broadcaster, interfaces, publishers |
| Controller inactive | ros2_control | manager logs, hardware state, claims |
| Plan fails | MoveIt | group, current state, collision, IK |
| Plan succeeds, no execute | mapping | MoveIt controller YAML, action list |
| Goal rejected | action contract | joints/order, tolerances, state |
| Goal aborted | execution/feedback | result, limits, feedback |
| Executor already spinning | application | executor ownership, callback groups |
| RViz drops messages | timing/load | timestamps, QoS, CPU, sim time |
| Gazebo instability | inertial/control | inertia, damping, update rate |
