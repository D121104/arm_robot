# TF and inertial guidance

Typical chain:

```text
world → base_link → arm links → flange → tool0 → tcp
```

Do not create duplicate publishers for one transform. Static transforms represent
rigid relationships only.

Every non-fixed simulated link should have plausible mass and a positive inertia
matrix. Avoid zero mass, zero diagonal inertia or extreme center-of-mass offsets.
State approximations and units explicitly.
