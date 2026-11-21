# Engineering Sources — Curation and Rights

**Date:** 21 November 2026
**Purpose:** record which sources are actually available, under what rights, and for what each may be used. Absence of a source is recorded as a blocker, not filled with an invented citation.

## 1. Sources used or verified

| Source | Type | Access / rights status | Verified on | Use |
|---|---|---|---|---|
| TracingInsights 2025 repository — <https://github.com/TracingInsights-Archive/2025> | Public telemetry dataset | Apache-2.0; README permits research, academic work, visualization and personal applications; no API key | 2026-11-21 | Real cached lap fixture for the MVP |
| TracingInsights README / data page | Dataset documentation | Same repository license | 2026-11-21 | Channel list, data caveats, provenance |
| FastF1 documentation — <https://docs.fastf1.dev/> | Library documentation | MIT (FastF1 3.9.2); docs describe channels, sampling, distance derivation, ±10 m overlap caveat | 2026-11-21 | Data dictionary and feature-spec caveats |
| FastF1 authentication docs — <https://docs.fastf1.dev/api_reference/accounts_auth.html> | Documentation | MIT | 2026-11-21 | Explains why live F1 data now requires an account |
| OpenF1 documentation — <https://openf1.org/docs/> | API documentation | Free historical tier described; API host was unreachable from this network | 2026-11-21 | Candidate provider, rejected for this environment |
| OpenStax, *College Physics 2e* — <https://openstax.org/details/books/college-physics-2e> | Open textbook | CC BY-NC-SA 4.0 (non-commercial, share-alike) | 2026-11-21 | Physics references for kinematics, energy, friction, circular motion |
| NASA Glenn, *Beginner's Guide to Aeronautics — What is Drag?* — <https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/what-is-drag/> | Government educational page | U.S. Government work, generally public domain | 2026-11-21 | Drag concept reference; page timed out on one fetch, URL retained from the official redirect notice |

## 2. Sources not obtained

| Source | Status | Consequence |
|---|---|---|
| Gillespie, *Fundamentals of Vehicle Dynamics* | Not obtained; no licensed copy available in the workspace | Vehicle-dynamics notes remain introductory; no page-level citation is claimed |
| Milliken & Milliken, *Race Car Vehicle Dynamics* | Not obtained | Same |
| Carroll Smith, *Tune to Win* | Not obtained; also secondary for physical setup | Not used |
| Official F1 live timing streams | HTTP 401 without an F1 account (requirement introduced October 2026) | Live ingestion is blocked; cached public fixture used |
| OpenF1 API | Host unreachable from this network | Not used |

## 3. Rules followed

- No pirated PDFs were downloaded.
- No copyrighted text was copied into the corpus. The engineering notes are original prose with references.
- The corpus separates regulation, telemetry data dictionary and engineering notes by role.
- Dataset hashes and retrieval dates are recorded in `datasets/telemetry/manifest.json`.
- If a licensed book becomes available later, it must be added with a rights entry before indexing.
