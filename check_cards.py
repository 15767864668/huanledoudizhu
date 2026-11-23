"""Diagnose the current WeChat mini-program image and legacy card templates.

Run: python check_cards.py
     python check_cards.py --image test_screen.png

Outputs:
  debug_full.png  normalized 1040x629 capture (only when capturing live)
  debug_hand.png  normalized landlord/bottom cards region
  a table of best correlations against the 2021 templates
"""
import argparse
from pathlib import Path

import cv2

from util.screen import screen
from vo.Poker import Poker

TEMPLATE_FILES = {
    "王": "dawang.png",
    "2": "fangkuai_2.png",
    "A": "fangkuai_a_b.png",
    "K": "fangkuai_k_1.png",
    "Q": "fangkuai_q_b.png",
    "J": "fangkuai_j_b.png",
    "10": "fangkuai_10_b.png",
    "9": "fangkuai_9_b.png",
    "8": "fangkuai_8_b.png",
    "7": "fangkuai_7.png",
    "6": "fangkuai_6_b.png",
    "5": "fangkuai_5.png",
    "4": "fangkuai_4.png",
    "3": "fangkuai_3_b.png",
}

def run(image_path=None):
    if image_path:
        img = cv2.imread(str(image_path))
        if img is None:
            raise RuntimeError("无法读取图片：" + str(image_path))
        img = cv2.resize(img, (1040, 629))
    else:
        img = screen()
        if img is None:
            raise RuntimeError("无法截屏，请保持腾讯欢乐斗地主窗口可见且未最小化")
        cv2.imwrite("debug_full.png", img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bottom_cards = gray[100:150, 470:565]
    cv2.imwrite("debug_hand.png", bottom_cards)
    print("截图尺寸：", img.shape, "底牌区域尺寸：", bottom_cards.shape)
    print("提示：此处是模板相似度测试，不代表自动识牌已完成。")
    print("牌型  相似度  位置    阈值0.80")
    for name, filename in TEMPLATE_FILES.items():
        t = cv2.imread(str(Path("templete") / filename), cv2.IMREAD_GRAYSCALE)
        if t is None:
            print(f"{name:>3}  模板缺失: {filename}")
            continue
        template = Poker(name, t).handImg
        if (template.shape[0] > bottom_cards.shape[0] or
                template.shape[1] > bottom_cards.shape[1]):
            print(f"{name:>3}  模板大于识别区域")
            continue
        response = cv2.matchTemplate(bottom_cards, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, position = cv2.minMaxLoc(response)
        print(f"{name:>3}  {score:.4f}  {position}  {'通过' if score >= 0.80 else '未通过'}")
    print("底牌截图：debug_hand.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="已有的截图文件；不传则读取当前可见游戏窗口")
    args = parser.parse_args()
    run(args.image)
