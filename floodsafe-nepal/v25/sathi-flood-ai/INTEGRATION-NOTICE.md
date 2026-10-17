# Integration notice

The stable FloodSafe Nepal V25 page is deliberately **not** modified in this branch.

The SATHI prototype runs from its own wrapper page and reads V25 through a same-origin iframe. This protects the already-working map, river, weather, alerts, news, and UI code from accidental changes.

A production merge into the stable V25 entrypoint would require a deliberate integration step later. That step is intentionally excluded from this branch.
