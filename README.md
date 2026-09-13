# FlyBrain / Elden Ring

[![tests](https://github.com/bubblik525/elden_ring/actions/workflows/tests.yml/badge.svg)](https://github.com/bubblik525/elden_ring/actions/workflows/tests.yml)

**A fly-inspired neural control project for Elden Ring.**

The architecture defines a closed loop: game observations become sensory inputs, a neural model produces motor signals, and a controller translates those signals into game actions. Each action changes the next observation.

**Status:** controller integration is pending. The current release provides a small spiking model, recorded-input telemetry and fly animation tools. Autonomous gameplay has not been demonstrated.

![Malenia instrumentation preview](assets/production-preview.jpg)

*Current instrumentation preview. The architecture and component status are documented below.*

## Controller architecture

1. **Observe** the game through a live frame adapter.
2. **Encode** visual features into sensory currents.
3. **Integrate** neural activity across successive observations.
4. **Decode** motor activity into movement, dodge, attack and interaction commands.
5. **Execute** bounded key presses and feed the next observation back into the model.

```mermaid
flowchart LR
  G[Game observations] --> S[Sensory encoder]
  S --> N[Neural state]
  N --> M[Motor decoder]
  M --> K[Keyboard controller]
  K --> G
  N --> T[Telemetry]
  K --> T
```

This diagram describes the controller design. The existing 96-unit fixed-weight LIF network is a starting component, not a biological fly connectome. The current release does not include the live encoder, motor decoder or keyboard controller.

## Run it

Python 3.11 or newer. From the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m eldenfly demo --output runs/demo
python -m pytest -q
```

These commands run the existing calibration demo and tests. Outputs include `replay.mp4`, `preview.png` and `telemetry.jsonl`. The package name remains `eldenfly`. The current CLI provides demo, analysis and rendering commands; it does not expose live game control.

## Component status

| Component | Responsibility | Status |
| --- | --- | --- |
| Neural core | Integrate input currents and emit spikes | Available: 96-unit LIF model |
| Telemetry | Record observed inputs and neural activity | Available for recorded inputs |
| Live observation adapter | Capture timestamped game frames | Not implemented |
| Sensory encoder | Convert scene features into neural inputs | Not implemented |
| Motor decoder | Map neural outputs to game actions | Not implemented |
| Keyboard controller | Execute, limit and release key presses | Not implemented |
| Closed-loop evaluation | Measure outcomes across repeatable encounters | Not implemented |

Controller acceptance requires a reproducible observation-to-action cycle with timestamped logs and key release on stop. Encounter evaluation requires an integrated controller.

## Development

```text
eldenfly/inputs.py       input sampling and press events
eldenfly/neural.py       spiking neural core
eldenfly/cli.py          existing demo and telemetry commands
eldenfly/render.py       instrumentation panel
eldenfly/production.py   production argument and asset validation
scripts/                Malenia composition pipeline
tests/                  detection, integration and export checks
```

See [model details](docs/model.md), [calibration](docs/calibration.md), [production tooling](docs/production.md) and [validation](docs/validation.md) for the current implementation. Existing rendering commands are in [the rendering guide](docs/rendering.md).

## Acknowledgments

[Stonkfly](https://github.com/nftechie/stonkfly) inspired the separation of sensory input, neural state and action execution. Fly rendering uses externally supplied [flybody](https://github.com/TuragaLab/flybody) assets. Neither project's source or connectome data is bundled here.

MIT-licensed code. See [third-party materials](THIRD_PARTY.md) for asset details. Independent of FromSoftware and Bandai Namco.
