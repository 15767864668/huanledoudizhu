"""Adaptive OpenCV rank recognition for the current WeChat mini-program.

Unlike the 2021 implementation, candidates are deduplicated across rank templates
and scales. Returns [] when confidence is insufficient rather than inventing cards.
This is an experimental detector; templates still require real-game calibration.
"""
from collections import Counter
import cv2
import numpy as np

def detect_cards(region, templates, threshold=0.76, scales=(0.75, 0.85, 1.0, 1.15, 1.3)):
    if region is None or region.size == 0:
        return []
    if region.ndim == 3:
        region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    candidates = []
    for poker in templates:
        base = poker.otherImg
        if base is None or base.size == 0:
            continue
        for scale in scales:
            w = max(4, int(base.shape[1] * scale))
            h = max(4, int(base.shape[0] * scale))
            if w > region.shape[1] or h > region.shape[0]:
                continue
            tpl = cv2.resize(base, (w, h), interpolation=cv2.INTER_AREA)
            if np.std(tpl) < 3:
                continue
            result = cv2.matchTemplate(region, tpl, cv2.TM_CCOEFF_NORMED)
            kernel = np.ones((max(3, h // 3), max(3, w // 3)), np.uint8)
            peaks = (result >= threshold) & (result == cv2.dilate(result, kernel))
            ys, xs = np.where(peaks)
            for y, x in zip(ys, xs):
                candidates.append((float(result[y, x]), poker.name, int(x), int(y), w, h))
    candidates.sort(reverse=True)
    accepted = []
    for score, name, x, y, w, h in candidates:
        # One winner per printed rank glyph, regardless of scale or template.
        if any(abs(x - a[2]) < max(9, min(w, a[4]) // 2)
               and abs(y - a[3]) < max(9, min(h, a[5]) // 2)
               for a in accepted):
            continue
        accepted.append((score, name, x, y, w, h))
    accepted.sort(key=lambda item: item[2])
    return [{"name": name, "num": 1, "x": x, "score": round(score, 3)}
            for score, name, x, y, w, h in accepted]

def combine_cards(cards):
    counts = Counter(card["name"] for card in cards)
    positions = {}
    for card in cards:
        positions[card["name"]] = min(positions.get(card["name"], card["x"]), card["x"])
    return [{"name": name, "num": count, "x": positions[name]}
            for name, count in counts.items()]
