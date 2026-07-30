# Planning and execution

Classify failures:

1. State acquisition: no recent joint states.
2. Start-state validity: limits or collision.
3. IK/planning: solver, constraints, scene or pipeline.
4. Controller selection: no matching controller.
5. Action execution: rejected, aborted or timed out.
6. Feedback: motion command runs but state feedback is wrong.

Capture exact error codes and states before changing planner parameters.
