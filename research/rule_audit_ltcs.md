# Audit — LTCS 2 kg Heat Hazard Rule (C4.6)

**Date:** 21 November 2026
**Rule:** `FIA26-C4.6-HEAT-INCREASE-LTCS-COMPETITION`
**Source:** FIA 2026 Section C Issue 21, Article C4.6, page 60.
**Status:** rule remains `reviewed`, `human_approved: false`; this audit is internal, not a human sign-off.

## Source text

> During a Competition at which a Heat Hazard has been declared for any session; For any LTCS or TTCS for which a Heat Hazard has not been declared:
> c. A Heat Hazard Mass Increase of 2kg will be applied.

## Finding

The previous rule applied the 2 kg increase to any LTCS when the Competition Heat Hazard was declared, without checking whether a Heat Hazard was declared for the session. The source sentence conditions the 2 kg increase on “LTCS or TTCS for which a Heat Hazard has not been declared”.

## Change

Added a condition to the rule:

```
heat_hazard_declared == false
```

The rule still applies only when:

- `competition_heat_hazard_declared == true`, and
- `session_category == "LTCS"`, and
- `heat_hazard_declared == false`.

## Regression checks

- Existing case `TC18` (LTCS, competition heat hazard, session heat hazard false) still returns 2 kg and remains VIOLATED at 797.5 kg.
- New test: LTCS with session heat hazard `true` returns `UNKNOWN` for `heat_hazard_mass_increase`, not 2 kg.
- New test: LTCS with session heat hazard `false` returns 2 kg.
- Full compliance regression passed (including the 18-case dataset).

## Remaining ambiguity

The regulation explicitly assigns 5 kg only to a TTCS with a declared heat hazard, and 2 kg to an LTCS/TTCS without a session heat hazard. It does not explicitly state a value for an **LTCS with a session heat hazard declared**. The system now returns `UNKNOWN` for that combination instead of silently assuming 2 kg. A human reviewer should confirm this interpretation against the FIA document before the rule is promoted.
