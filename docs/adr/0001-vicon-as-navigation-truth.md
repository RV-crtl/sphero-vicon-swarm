# ADR 0001: Use Vicon as navigation truth

**Status:** Accepted

## Decision

Use externally measured Vicon pose as the primary planar navigation state for closed-loop chariot motion.

## Rationale

Loaded robots experience wheel slip, static friction and chariot-specific dynamics that can make open-loop or onboard-distance estimates unreliable for precise world-frame trajectory tracking.

## Consequences

The controller depends on a healthy motion-capture stream and must handle occlusion/stale data explicitly.
