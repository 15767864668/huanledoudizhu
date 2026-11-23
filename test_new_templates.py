"""Experimental A/7 sample-template extraction from user's 95x50 AA7 bottom card crop.

This is a *same-image diagnostic*, not a production classifier. You need examples
from more games / colors before automatic scorekeeping can be trusted.

Place the previously captured debug_hand.png (containing A A 7) next to this file.
Run: python test_new_templates.py
"""
from pathlib import Path
import cv2
import numpy as np

source = cv2.imread("debug_hand.png", cv2.IMREAD_GRAYSCALE)
if source is None:
    raise SystemExit("缺少 debug_hand.png：请先在 A A 7 底牌可见时运行 check_cards.py")
if source.shape[:2] != (50, 95):
    raise SystemExit(f"样本尺寸不匹配：{source.shape}；需要以前保存的 95x50 A A 7 底牌截图")

output = Path("new_templates")
output.mkdir(exist_ok=True)
# Bounding rectangles around ranks, deliberately exclude suit symbols.
rectangles = {"A": (9, 6, 13, 19), "7": (56, 6, 13, 19)}
for label, (x, y, w, h) in rectangles.items():
    tile = source[y:y + h, x:x + w]
    cv2.imwrite(str(output / f"{label}.png"), tile)

def detect(image, template, threshold=0.92):
    scores = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(scores >= threshold)
    candidates = sorted(((float(scores[y, x]), int(x), int(y))
                         for y, x in zip(ys, xs)), reverse=True)
    picks = []
    for score, x, y in candidates:
        if all(abs(x - old_x) >= 12 or abs(y - old_y) >= 10
               for old_x, old_y in picks):
            picks.append((x, y))
    return sorted(picks)

print("仅测试相同样本图上的识别效果（不代表跨局识别准确率）")
for label in rectangles:
    template = cv2.imread(str(output / f"{label}.png"), 0)
    matches = detect(source, template)
    print(f"{label}: 检测 {len(matches)} 个，位置 {matches}")
print(f"模板已保存到：{output.resolve()}")
