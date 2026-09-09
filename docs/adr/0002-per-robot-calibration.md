# ADR 0002: Calibrate each robot independently

**Status:** Accepted

## Decision

Measure at least two non-collinear world displacement vectors for each robot and derive an individual heading basis.

## Rationale

A shared fixed heading offset is fragile when chariot mounting, robot aiming or coordinate conventions differ.

## Consequences

Hardware runs take longer to start, but steering becomes traceable to measured motion rather than an assumed frame mapping.
