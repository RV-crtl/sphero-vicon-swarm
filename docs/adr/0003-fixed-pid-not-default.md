# ADR 0003: Do not make one fixed PID tuning the default

**Status:** Accepted

## Decision

Do not publish one universal P/PD/PID gain set as the default control solution.

## Rationale

Experimental runs showed meaningful variation in breakaway, overshoot and damping between loaded chariots and between runs. Fixed gains remain useful for controlled experiments, but the reusable architecture should emphasise measured state, calibration, geometry and bounded correction.

## Consequences

Control parameters still require tuning, but the repository avoids implying that one numerical PID triplet is portable across hardware setups.
