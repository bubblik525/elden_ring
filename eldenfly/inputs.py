"""Read yellow highlights from one calibrated 1920x1080 keyboard overlay."""
from dataclasses import dataclass
import numpy as np

CENTERS = {
    "TAB": (1310, 158), "Q": (1410, 158), "W": (1507, 158),
    "E": (1598, 158), "R": (1690, 158), "SHIFT": (1310, 250),
    "A": (1410, 250), "S": (1507, 250), "D": (1598, 250),
    "F": (1690, 250), "CTRL": (1310, 340), "SPACE": (1500, 340),
    "LMB": (1777, 218), "RMB": (1846, 218),
}
KEYS = tuple(CENTERS)
# The parry shield icon can obscure F. Sample its four highlighted corners.
F_CORNERS = ((1730, 217), (1648, 282), (1668, 218), (1720, 280))

@dataclass(frozen=True)
class InputState:
    keys: tuple[str, ...]
    scores: dict[str, float]


def yellow_fraction(patch: np.ndarray) -> float:
    if not patch.size:
        return 0.0
    r, g, b = patch.astype(float).transpose(2, 0, 1)
    mask = (r > 125) & (g > 125) & (b < .78 * np.minimum(r, g)) & (abs(r-g) < 65)
    return float(mask.mean())


class OverlayDetector:
    """Fixed-layout colour measurement, not a learned detector or OCR model.

    Scores are yellow-pixel fractions, not confidence probabilities.
    Frames must contain the complete overlay and share its reference layout.
    """
    def __init__(self, threshold: float = .30):
        if not 0 < threshold < 1:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold

    def detect(self, frame: np.ndarray) -> InputState:
        if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
            raise ValueError("frame must be an HxWx3 uint8 RGB image")
        h, w, _ = frame.shape
        if w < 480 or h < 270:
            raise ValueError("frame is too small for this overlay profile")
        sx, sy = w/1920, h/1080
        def patch(x, y, rx, ry):
            x, y = round(x*sx), round(y*sy)
            rx, ry = max(1, round(rx*sx)), max(1, round(ry*sy))
            return frame[max(0,y-ry):min(h,y+ry), max(0,x-rx):min(w,x+rx)]
        scores = {key: yellow_fraction(patch(x, y, 24, 27))
                  for key, (x, y) in CENTERS.items()}
        scores["F"] = float(np.median([
            yellow_fraction(patch(x,y,4,4)) for x,y in F_CORNERS]))
        return InputState(tuple(k for k in KEYS if scores[k] > self.threshold), scores)


def rising_edges(previous: tuple[str, ...], current: tuple[str, ...]) -> tuple[str, ...]:
    """Held buttons do not create duplicate press events."""
    return tuple(k for k in current if k not in previous)
