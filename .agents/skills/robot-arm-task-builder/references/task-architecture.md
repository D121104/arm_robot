# Task architecture

Use the simplest sufficient abstraction. A single pose move does not require a
complex task framework. Multi-stage tasks with grasp generation, scene attachment
and recovery may benefit from MoveIt Task Constructor or an explicit state machine.

Actions should provide stage feedback and distinguish invalid requests, planning
failure, execution failure, cancellation, timeout and safety interlock.
