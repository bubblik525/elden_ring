# Rendering guide

Run these commands from the repository root after installing the package.

## Process a recording

```sh
python -m eldenfly analyze gameplay.mp4 --seconds 60 --output runs/session
python -m eldenfly render gameplay.mp4 --seconds 60 --output runs/render
```

The keyboard detector reads the yellow input overlay in the Malenia recording profile. It supports uniform resizing; a different layout needs [calibration](calibration.md). The lightweight renderer exports silent video and drives a deterministic 96-unit integrate-and-fire network from observed button states.

## Production render

Install FFmpeg and the optional renderer dependencies:

```sh
pip install -e '.[cinema,test]'
git clone https://github.com/TuragaLab/flybody.git vendor/flybody
git -C vendor/flybody checkout d015e9bfe441bd90ae431bac24c55cb74bdbce26

python scripts/malenia_scene.py \
  --input malenia.mp4 \
  --brain brain-reference.png \
  --fly-assets vendor/flybody/flybody/fruitfly/assets \
  --output runs/scene --seconds 60

python scripts/malenia_guidance.py \
  --input runs/scene/Malenia-Fly-Keyboard-Sync.mp4 \
  --telemetry runs/scene/observed-inputs.json \
  --output runs/guidance --seconds 60
```

This exports 1920×1080 video at 24 fps with source audio when available. Use `--seconds 2` in both commands for a smoke render. The production composition is calibrated to the original Malenia clip and the supplied brain projection; see [assets, timing and setup](production.md).

