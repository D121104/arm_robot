# Pick-and-place checklist

- Object pose/frame and dimensions are known.
- TCP and grasp frame are defined.
- Gripper targets are valid.
- Approach/retreat directions use the intended frame.
- Touch links are limited to legitimate gripper links.
- Attach only after successful grasp; detach after release.
- Plans account for the attached object.
- Every stage supports timeout, cancellation and clear errors.
