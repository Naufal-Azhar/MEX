# Rule Validation Log

Generated: 2026-11-17T05:45:44.443358+00:00

Automated source check only. Rules remain `reviewed` and are **not** human-approved. The system therefore reports them as demo-only.

| Rule | Goal | Article | Page | Status | Quote check | Human approved | Reviewer | Test cases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FIA26-C2.3.1-HALF-WIDTH | half_width_compliance | C2.3.1 | 10 | reviewed | PASS | False | internal_agent_check | TC03, TC08 |
| FIA26-C2.3.3-WHEELBASE | wheelbase_compliance | C2.3.3 | 11 | reviewed | PASS | False | internal_agent_check | TC01, TC06, TC11 |
| FIA26-C2.3.5-COCKPIT-POSITION | cockpit_position_compliance | C2.3.5 | 11 | reviewed | PASS | False | internal_agent_check | TC02, TC07, TC12 |
| FIA26-C4.1-BASE-MASS-Q | base_minimum_mass | C4.1 | 59 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.1-BASE-MASS-OTHER | base_minimum_mass | C4.1 | 59 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.6-HEAT-INCREASE-TTCS-DECLARED | heat_hazard_mass_increase | C4.6 | 60 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.6-HEAT-INCREASE-LTCS-COMPETITION | heat_hazard_mass_increase | C4.6 | 60 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.6-HEAT-INCREASE-TTCS-NOT-DECLARED | heat_hazard_mass_increase | C4.6 | 60 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.6-HEAT-INCREASE-NONE | heat_hazard_mass_increase | C4.1 | 59 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.1-MINIMUM-MASS-VALUE | minimum_mass | C4.1 | 59 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.2-MINIMUM-MASS-NO-HEAT | minimum_mass_excluding_heat_hazard | C4.2 | 59 | reviewed | PASS | False | internal_agent_check | TC05, TC10, TC15 |
| FIA26-C4.1-MINIMUM-MASS | minimum_mass_compliance | C4.1 | 59 | reviewed | PASS | False | internal_agent_check | TC04, TC09, TC13, TC14, TC16, TC17, TC18 |
| FIA26-C4.2-MASS-DISTRIBUTION | mass_distribution_compliance | C4.2 | 59 | reviewed | PASS | False | internal_agent_check | TC05, TC10, TC15 |

## Rule notes

- `FIA26-C2.3.1-HALF-WIDTH`: Tyres, wheel rims, and parts attached to wheel rims (C10.7.6) are excluded; the fact is defined as already excluding them.
- `FIA26-C2.3.3-WHEELBASE`: Planes XF/XR are defined in Article C2.2.
- `FIA26-C2.3.5-COCKPIT-POSITION`: Planes XA=0 (forward limit of the Survival Cell) and XC=0 (rear of the Cockpit) are defined in Article C2.2.
- `FIA26-C4.1-BASE-MASS-Q`: -
- `FIA26-C4.1-BASE-MASS-OTHER`: -
- `FIA26-C4.6-HEAT-INCREASE-TTCS-DECLARED`: -
- `FIA26-C4.6-HEAT-INCREASE-LTCS-COMPETITION`: -
- `FIA26-C4.6-HEAT-INCREASE-TTCS-NOT-DECLARED`: -
- `FIA26-C4.6-HEAT-INCREASE-NONE`: This rule encodes the absence of an increase, inferred from C4.1: the increase applies only when a Heat Hazard has been declared. The quote is the exact C4.1 sentence; no numeric amount is invented.
- `FIA26-C4.1-MINIMUM-MASS-VALUE`: Nominal Tyre Mass is not a fixed number in the regulations; it must be supplied as a fact (C4.7, Appendix C1). The Heat Hazard increase is quoted and validated separately by the C4.6 subgoal rules.
- `FIA26-C4.2-MINIMUM-MASS-NO-HEAT`: Deliberately separate from goal 'minimum_mass' so that the C4.2 exclusion is explicit in the trace.
- `FIA26-C4.1-MINIMUM-MASS`: -
- `FIA26-C4.2-MASS-DISTRIBUTION`: -

## Sign-off

Reviewer: ____________________  Date: ____________

To activate a rule, set `human_approved: true`, add `reviewer` and `reviewed_at`, then change its status from `reviewed` to `active`.
