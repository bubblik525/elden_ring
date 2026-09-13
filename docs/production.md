# Production pipeline

The two scripts were adapted from the local renderers used for the Malenia demo. Changes make paths configurable, select available fonts, limit duration, validate inputs and check video encoding. Original source hashes are recorded in [production-provenance.json](production-provenance.json).

## Assets and setup

- Python 3.11+, NumPy, Pillow, MuJoCo and FFmpeg on PATH.
- A working OpenGL context for MuJoCo. The production smoke render was checked on macOS; headless Linux may require platform-specific EGL/OSMesa setup. Production rendering is not run by CI.
- External flybody assets at commit `d015e9bfe441bd90ae431bac24c55cb74bdbce26`; pass the folder containing `fruitfly.xml` and its meshes.
- The original 1920×1080 Malenia recording, with its yellow keyboard overlay in the upper-right area. It is not bundled.
- A locally supplied 640×942 brain/ventral-nerve-cord projection, matching the demo reference. The point sampler uses brightness above 62 and a fixed projection transform; other images require adjusting this transform.

Run the two commands in the README from the repository root after installing the package. Each output directory must be new or empty. Duration must be greater than zero and at most 60 seconds; it is rounded to a 24 fps frame boundary. The second pass needs at least that many telemetry frames and matching video frames.

## Timing and outputs

The scene profile stretches source time by 1.2278 and applies `atempo=0.81447` to audio. This maps the approximately 48.9-second source to a minute. It is a clip-specific composition, not a general automatic scene editor. The lightweight CLI keeps source playback timing instead.

The scene pass writes `Malenia-Fly-Keyboard-Sync.mp4`, `observed-inputs.json`, selected JPEG previews and an intermediate `silent.mp4`. The guidance pass writes `Malenia-Neural-Red-Guidance.mp4`, `cue-events.json`, previews and its own intermediate. Both final exports retain an optional source audio stream.

## Implementation boundaries

The keyboard layer measures yellow-highlight fractions in fixed image regions. Rising edges are computed from these states. The production renderer maps observed keys to scripted MuJoCo joint poses and calls forward kinematics; it does not run a learned locomotion controller.

The supplied brain picture is sampled into animated points. This production layer is an artistic activity projection, separate from the small fixed-weight LIF model in `eldenfly/neural.py`. Neither is a reconstructed biological connectome.

Boss rectangles use clip-specific annotation coordinates and visual heuristics. Input countdowns look ahead in recorded telemetry. Action names reflect the demo's key mapping. These layers do not establish live character recognition, future-action prediction, training, autonomous game control or biological gameplay ability.

The code actually renders these visualizations. It does not claim to have controlled the recorded playthrough. Stonkfly inspired the separation of inputs, network state and output; its source and datasets are not included.
