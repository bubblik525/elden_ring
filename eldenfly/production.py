"""Portable argument and asset checks for the original cinematic renderers."""
import argparse
import json
import math
import shutil
from pathlib import Path
from PIL import ImageFont


def font(size, mono=False):
    candidates = (["/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
                  if mono else ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def frame_count(seconds):
    if not math.isfinite(seconds) or not 0 < seconds <= 60:
        raise ValueError("seconds must be finite, greater than 0 and at most 60")
    return max(1, round(seconds * 24))


def arguments(stage):
    p = argparse.ArgumentParser(description=f"Malenia production renderer: {stage}")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=60)
    if stage == "scene":
        p.add_argument("--brain", type=Path, required=True)
        p.add_argument("--fly-assets", type=Path, required=True,
                       help="flybody/fruitfly/assets directory containing fruitfly.xml and meshes")
    else:
        p.add_argument("--telemetry", type=Path, required=True)
    a = p.parse_args()
    try:
        a.count = frame_count(a.seconds)
        a.seconds = a.count / 24
        if not a.input.is_file():
            raise ValueError(f"Input video not found: {a.input}")
        if shutil.which("ffmpeg") is None:
            raise ValueError("FFmpeg is required on PATH")
        if stage == "scene":
            if not a.brain.is_file():
                raise ValueError(f"Brain reference not found: {a.brain}")
            if not (a.fly_assets / "fruitfly.xml").is_file():
                raise ValueError("fly-assets must contain fruitfly.xml")
        elif not a.telemetry.is_file():
            raise ValueError(f"Telemetry not found: {a.telemetry}")
        # New output directories prevent accidental mixing of renders.
        if a.output.exists() and any(a.output.iterdir()):
            raise ValueError("Choose a new or empty output directory")
        a.output.mkdir(parents=True, exist_ok=True)
    except ValueError as e:
        p.error(str(e))
    return a


def read_telemetry(path, count):
    records = json.loads(Path(path).read_text())
    if len(records) < count:
        raise ValueError(f"Need {count} telemetry frames, found {len(records)}")
    for i, row in enumerate(records):
        if row.get("frame") != i or not isinstance(row.get("keys"), list):
            raise ValueError("Telemetry must have consecutive frame indices and key lists")
    return records
