# SATHI Flood AI — Additive Module

This directory is intentionally isolated from the existing FloodSafe Nepal V25 code.

## Non-negotiable rule
- Existing FloodSafe Nepal files are not modified by this module.
- River, map, alert, weather, news, and UI runtimes remain untouched.
- SATHI reads only from the public runtime state exposed by the existing app.

## Scope
- Flood/river/rain/weather-risk questions only.
- Default answers in Nepali (Devanagari), including when the user asks in Roman Nepali.
- No fabricated flood status. If current official data is unavailable, the assistant says so clearly.
- River answers read current BIPAD/DHM state already exposed by FloodSafe.
- Rain timing answers read the existing FloodSafe rain forecast state.

## Planned integration
This branch only adds an isolated module. It is not loaded by the stable V25 page yet, because loading it would require changing an existing file. Integration can be done later only with explicit permission.
