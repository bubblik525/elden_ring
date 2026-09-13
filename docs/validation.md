# Validation

Local validation on September 13, 2026: macOS, Python 3.14.

- `python -m pytest -q`: **14 passed**.
- `python -m eldenfly demo --seconds 4`: 120 samples, 2,776 simulated spikes; MP4 and preview written.
- A local 1920x1080 Malenia recording was processed for four seconds at 24 samples/s: 96 samples, 2,446 simulated spikes.
- The integration tests decode exported video frames, check image dimensions and verify that rendering a 5 fps source at a requested 30 fps preserves its 5 fps playback rate.

The shipped GitHub Actions workflow provides independent Python 3.11–3.13 checks. The workflow badge links to its actual status.

These checks establish software behavior, not biological realism or gameplay ability. They do not validate general-purpose recognition of arbitrary keyboards, objects or opponents. No benchmark accuracy, autonomous boss kill, live inference latency or learning result is claimed.

## Production renderer validation

After adding the production scripts, the local suite reports **22 passed**.
Both production passes were executed on a two-second segment of the original
Malenia recording with the supplied brain reference and pinned flybody assets.
The final export was visually inspected and fully decoded by FFmpeg without
errors: H.264, 1920×1080, 24 fps, AAC audio, 2.000 seconds. This smoke check covers
the render and mux path; it is not a new full-minute rerender or a cross-platform
MuJoCo rendering check. Production helper tests run in the regular CI suite.
