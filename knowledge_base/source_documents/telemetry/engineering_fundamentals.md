# Engineering Fundamentals Notes — Telemetry Interpretation

**Status:** self-authored educational notes for MEX-AI. These are explanatory notes, not normative engineering standards and not vehicle-specific measurements.
**Purpose:** supply grounded theory for the Engineering Tutor and for rule-source mapping without copying copyrighted textbooks.
**Rights:** this note is original text written for this project. Referenced works remain under their own licenses; no text is reproduced from them.

## 1. Speed, distance and time

For a point moving along a path, instantaneous speed is the rate of change of distance:

```
v = ds / dt
```

With discrete telemetry samples, a finite-difference approximation is:

```
v_avg = (s2 - s1) / (t2 - t1)
a_approx = (v2 - v1) / (t2 - t1)
```

`a_approx` is a change in speed per unit time along the path. It is **not** a direct accelerometer measurement and it does not separate longitudinal acceleration from path curvature or gradient effects. Convert km/h to m/s before computing it.

Reference: OpenStax, *College Physics 2e*, chapters on kinematics (CC BY-NC-SA 4.0). <https://openstax.org/details/books/college-physics-2e>

## 2. Braking

Under an idealised constant deceleration `a` (negative), the stopping distance from speed `v` is:

```
d = v^2 / (2 * |a|)
```

and the kinetic energy that must be dissipated is:

```
E_k = 0.5 * m * v^2
```

Two consequences matter for telemetry learning:

1. Braking distance grows with the square of entering speed. A car entering a corner faster must brake earlier or harder, or both.
2. The brake channel marks **when the driver applies the brake**, not how much pressure is applied. A later brake onset is not automatically better: it may be enabled by higher grip, a different line, a tow, or a different entry speed.

Reference: OpenStax, *College Physics 2e*, chapters on work, energy and energy conservation; Newton's laws and friction.

## 2.1 Brake onset

**Brake onset** is the first sample of a sustained brake-on interval after a debounce rule. It is a timing marker, not a brake-pressure measurement.

For this project, onset is reported with:

- distance from the start of the lap, in metres;
- elapsed time from the start of the lap, in seconds;
- the speed and throttle value at that sample.

A debounce of at least two samples is used so that a single noisy sample is not treated as a braking event. The delta between two laps is **B minus A**; a positive delta means B applied the brake later at the compared point. The marker does not describe brake pressure, brake temperature, pedal force, or the driver's intention.

Reference: original MEX-AI telemetry notes; no external text reproduced.

## 3. Throttle

The throttle channel is pedal input percentage. It is not engine power, torque, or energy deployment. At 100% throttle the power delivered still depends on engine mapping, gear, speed, ERS state and traction limits. Therefore:

- throttle onset can describe driver input timing;
- it cannot by itself explain acceleration differences;
- a earlier throttle application is not automatically faster if the car is still grip-limited.

## 4. Grip, load transfer and tyres

Tyre grip depends on the tyre, temperature, pressure, wear, surface and normal load. Under braking, load transfers toward the front axle; under acceleration, toward the rear. Aerodynamic downforce increases normal load with speed, which can increase available grip.

Without tyre state, aerodynamic maps, suspension data and mass distribution, a telemetry-only comparison cannot attribute a difference to grip, downforce, setup or driver technique. These remain candidate explanations, not conclusions.

Reference: OpenStax, *College Physics 2e*, chapters on Newton's laws, friction and circular motion. For vehicle dynamics beyond introductory physics, see the source list in `research/engineering_sources.md`.

## 5. Drag and aero limits

The drag force on a body is commonly modelled as:

```
F_drag = 0.5 * rho * v_air^2 * C_d * A
```

where `rho` is air density, `v_air` is airspeed, `C_d` is the drag coefficient and `A` is reference area. Speed alone does not determine `C_d`, `A`, or drag power; those variables are not present in the public telemetry fixture. The formula is used for education only. The system must not estimate a car's drag coefficient from speed.

Reference: NASA Glenn Research Center, *Beginner's Guide to Aeronautics — What is Drag?* (U.S. Government work). <https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/what-is-drag/>

## 6. What telemetry can and cannot support

Supported descriptive statements:

- Car A reached a higher maximum speed in the measured segment.
- Car B applied the brake at a larger distance from the start/finish line in the measured lap.
- The speed difference at a given distance was X km/h.
- The measured data contains a gap or a missing channel.

Not supported without additional evidence:

- Driver B is more skilled.
- Car A has more downforce or less drag.
- The setup caused the difference.
- The tyre was degraded in a specific way.
- The car would be faster or slower in another session.
- Any causal explanation of an understeer/oversteer diagnosis.
