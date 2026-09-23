# FloodSafe Nepal v0.8.79 — full river detail fix

Field-test fix for missing/disconnected river geometry on the native MapLibre map.

The old native geometry loader globally ranked the full Nepal waterway snapshot and retained only 1,400 ways. That could leave local river segments missing or disconnected even though the underlying progressive river assets existed.

v0.8.79 changes the runtime to use the bundled progressive assets:

- whole-Nepal view: balanced Nepal overview network
- regional zoom: nearby spatially balanced regional tiles
- local zoom: exact nearby river/stream tiles
- overlapping tile features are deduplicated by stable OSM id
- existing v0.8.78 station/readout resilience and alert freshness rules are retained

Validated in GitHub Actions run 35896323934. The coverage audit passed with source inventory 62,194, balanced overview 4,219, 96 exact tiles, 96 regional tiles, Kathmandu-area exact tile 2,479 waterways, and 77 district boundaries. Unit tests, native APK compile, APK integrity checks, required asset checks, and artifact upload also passed.
