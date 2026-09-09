# Safety

This repository can command physical robots. Treat every hardware run as an experiment with moving equipment.

## Pre-run checklist

- Clear people, cables and fragile equipment from the operating area.
- Confirm all robot/Vicon mappings.
- Confirm measured positions are current and not occluded.
- Use conservative speed for the first run after any hardware/configuration change.
- Keep `Ctrl+C`/terminal focus available.
- Know how to physically reach and stop the robots if software control fails.

## Software safety principles

- stop every robot in `finally`/context cleanup;
- reject stale or occluded tracking when it persists;
- use workspace margins before physical obstacles;
- reduce progression when cross-track/formation error is large;
- never rely on collision avoidance as the only barrier to contact.

The software is a prototype and is not safety-certified.
