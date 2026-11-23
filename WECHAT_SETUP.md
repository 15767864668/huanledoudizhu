# 微信电脑端欢乐斗地主记牌器 — 当前适配状态

## 安装
在 Windows 的项目目录执行：

```powershell
python -m pip install -r requirements.txt
python main.py
```

请保持微信小程序游戏窗口可见，避免其他窗口遮挡。

## 已更新
- 兼容“腾讯欢乐斗地主”与“欢乐斗地主”窗口标题。
- 使用 Pillow 截取游戏窗口，进行 DPI 坐标适配，并缩放到 1040×629。
- 更新了旧版界面字体和检测区域。
- 修复部分代码中意外写入的字面量反斜杠 n，补充 win32api 导入。
- 新增 `python check_cards.py` 截图及旧模板诊断；结果保存为项目根目录下的 `debug_full.png` 和 `debug_hand.png`。

## 尚未完成
旧版 OpenCV 模板在新版小程序上没有经过充分验证。底牌、手牌、出牌识别与剩余牌计数尚不能保证准确；检测区域是针对已有截图的近似值。诊断脚本不是自动记牌功能的替代品。

## 诊断
对局期间运行 `python check_cards.py`，检查 `debug/full.png` 和 `debug/bottom_cards.png`，并记录各模板匹配度。当前测试阈值 0.80，不建议为了通过测试而直接降低阈值。
