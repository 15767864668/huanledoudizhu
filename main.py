#!/usr/bin/python
# coding:utf-8

"""
@author: css
@software: PyCharm
@file: main.py
@time: 2021/3/3 16:32:04
"""
from vo.Poker import Poker
from util.adaptive_recognizer import detect_cards, combine_cards
from util.screen import *
from view.Window import (Window, QThread, pyqtSignal, time, QtWidgets)
from view.LogWindow import LogWindow
import sys
from collections import Counter
import win32com.client
import win32con
import win32api
import win32gui

hWnd = find_game_window()
continueGame = cv2.imread('templete/continue_game.png', 0)
# 0 没有出牌，1第一次检测到，2第二次检测到
isUpOut = 0
isDownOut = 0
isSelfOut = 0
# 0 结束，1 第一次开局，2 记牌中
status = -1
PokerList = [
    Poker('王', cv2.imread('templete/dawang.png', 0), 2),
    Poker('2', cv2.imread('templete/fangkuai_2.png', 0)),
    Poker('A', cv2.imread('templete/fangkuai_a_b.png', 0)),
    Poker('K', cv2.imread('templete/fangkuai_k_1.png', 0)),
    Poker('Q', cv2.imread('templete/fangkuai_q_b.png', 0)),
    Poker('J', cv2.imread('templete/fangkuai_j_b.png', 0)),
    Poker('10', cv2.imread('templete/fangkuai_10_b.png', 0)),
    Poker('9', cv2.imread('templete/fangkuai_9_b.png', 0)),
    Poker('8', cv2.imread('templete/fangkuai_8_b.png', 0)),
    Poker('7', cv2.imread('templete/fangkuai_7.png', 0)),
    Poker('6', cv2.imread('templete/fangkuai_6_b.png', 0)),
    Poker('5', cv2.imread('templete/fangkuai_5.png', 0)),
    Poker('4', cv2.imread('templete/fangkuai_4.png', 0)),
    Poker('3', cv2.imread('templete/fangkuai_3_b.png', 0))
    # Poker('王', cv2.imread('templete/dawang.png', 0), 2),
    # Poker('2', cv2.imread('templete/fangkuai_2_b.png', 0)),
    # Poker('A', cv2.imread('templete/fangkuai_a_b.png', 0)),
    # Poker('K', cv2.imread('templete/fangkuai_k_b.png', 0)),
    # Poker('Q', cv2.imread('templete/fangkuai_q_b.png', 0)),
    # Poker('J', cv2.imread('templete/fangkuai_j_b.png', 0)),
    # Poker('10', cv2.imread('templete/fangkuai_10_b.png', 0)),
    # Poker('9', cv2.imread('templete/fangkuai_9_b.png', 0)),
    # Poker('8', cv2.imread('templete/fangkuai_8_b.png', 0)),
    # Poker('7', cv2.imread('templete/fangkuai_7_b.png', 0)),
    # Poker('6', cv2.imread('templete/fangkuai_6_b.png', 0)),
    # Poker('5', cv2.imread('templete/fangkuai_5_b.png', 0)),
    # Poker('4', cv2.imread('templete/fangkuai_4_b.png', 0)),
    # Poker('3', cv2.imread('templete/fangkuai_3_b.png', 0))
]


class WindowThread(QThread):
    # 定义信号,定义参数为str类型
    breakSignal = pyqtSignal(int)

    # 子类的构造函数必须先调用其父类的构造函数，重写run()方法。
    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        while (True):
            time.sleep(0.2)
            self.breakSignal.emit(10)


class MyThread(QThread):
    breakSignal = pyqtSignal(list, list, object)
    statusSignal = pyqtSignal(int)

    # 子类的构造函数必须先调用其父类的构造函数，重写run()方法。
    def __init__(self):
        super().__init__()
        self.pending_hand = None
        self.hand_applied = False

    def set_initial_hand(self, ranks):
        # Set from the GUI thread; consumed by the worker on the next tick.
        self.pending_hand = list(ranks)

    def matchImgNum(self, bgImg, templeteImg, threshold=0.92, save=False):
        if (bgImg is None or templeteImg is None or bgImg.size == 0 or
                bgImg.shape[0] < templeteImg.shape[0] or
                bgImg.shape[1] < templeteImg.shape[1]):
            return 0, 0
        res = cv2.matchTemplate(bgImg, templeteImg, cv2.TM_CCOEFF_NORMED)
        # tt = bgImg.copy()
        # w, h = templeteImg.shape[::-1]
        loc = np.where(res >= threshold)
        num = 0
        last = 0
        if len(loc[0]) != 0:
            # 排序
            loc[1].sort()
            for point in loc[1]:
                if abs(last - point) > 5:
                    num += 1
                    # if save:
                    # print(save)
                    # for pt in zip(*loc[::-1]):
                    #     cv2.rectangle(tt, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
                    # cv2.imwrite('res22.png', tt)
                last = point

        return num, last

    def reset_round(self):
        """Clear previous-round counters and recognition history."""
        global status, isUpOut, isDownOut, isSelfOut
        status = 0
        self.hand_applied = False
        self.pending_hand = None
        isUpOut = isDownOut = isSelfOut = 0
        for poker in PokerList:
            poker.init()
        if hasattr(self, '_turn_state'):
            for state in self._turn_state.values():
                state.update(last=None, streak=0, latched=False, blank=0)
        self.statusSignal.emit(0)
        self.breakSignal.emit([], [], {})

    def main(self):

        global isUpOut
        global isDownOut
        global isSelfOut
        global status
        outList = {}
        templates = PokerList
        global hWnd
        hWnd = find_game_window()
        img_rgb = screen(hWnd)

        if img_rgb is None:
            return
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

        # Approximate regions measured from the current 715x495 mini-program layout.
        # The game is normalized to 1040x629 by util.screen.screen().
        selfCard = img_gray[410:595, 90:990]
        upotherCard = img_gray[185:370, 120:525]
        downotherCard = img_gray[185:370, 515:940]
        selfOutCard = img_gray[255:420, 240:810]
        handCard = img_gray[100:151, 470:560]
        # End-of-round detection is debounced. The old code only set status=0
        # and left the previous counters and per-turn latches untouched.
        if not hasattr(self, '_end_frames'):
            self._end_frames = 0
            self._clear_frames = 0
            self._wait_for_next_round = False
        end_matches, _ = self.matchImgNum(img_gray, continueGame, 0.74)
        if end_matches > 0:
            self._end_frames += 1
            self._clear_frames = 0
            if self._end_frames >= 2 and not self._wait_for_next_round:
                self.reset_round()
                self._wait_for_next_round = True
            return
        self._end_frames = 0
        if self._wait_for_next_round:
            self._clear_frames += 1
            # Wait for the result / continue overlay to disappear before
            # allowing the next round to initialize.
            if self._clear_frames < 3:
                return
            self._wait_for_next_round = False
            self._clear_frames = 0
        if status == -1:
            status = 0
        selfList = []
        upotherList = []
        downotherList = []
        # 自家出牌列表
        selfOutList = []
        handList = []
        for pokerObj in templates:
            if status > 0:
                # 判断手牌
                if status == 1:
                    # Legacy hand templates are uncalibrated. Never subtract an
                    # unverified partial hand: it corrupts all remaining counts.
                    pass
                    # if (num > 0):
                    # print(pokerObj.name, num, end='|')
                    # cv2.imwrite('aaa.png', selfCard)

                selfList.append(pokerObj.num)

            # 判断底牌
            num, x = self.matchImgNum(handCard, pokerObj.handImg, 0.8)
            if num > 0:
                for ind in range(num):
                    handList.append(pokerObj.name)

        if status > 0:
            upotherList = combine_cards(detect_cards(upotherCard, templates, threshold=0.83))
            downotherList = combine_cards(detect_cards(downotherCard, templates, threshold=0.83))
            selfOutList = combine_cards(detect_cards(selfOutCard, templates, threshold=0.83))

        if status == 1:
            status = 2
            self.statusSignal.emit(status)
        # The legacy bottom-card templates often fail on the current WeChat UI.
        # Use a conservative visual presence check to enter the round;
        # this does NOT assert that the ranks were recognized.
        bottom_roi = img_gray[101:145, 475:555]
        bright_ratio = float(np.mean(bottom_roi > 205)) if bottom_roi.size else 0.0
        bottom_visible = bright_ratio > 0.22
        if bottom_visible and status == 0:
            # print("开始")
            status = 1
            self.statusSignal.emit(status)
            # print("底牌")
            # print(handList)
            for pokerObj in templates:
                pokerObj.init()
            selfList = [pokerObj.num for pokerObj in templates]
            isUpOut = isDownOut = isSelfOut = 0
            self.hand_applied = False
            if hasattr(self, '_turn_state'):
                for st in self._turn_state.values():
                    st.update(last=None, streak=0, latched=False, blank=0)

        # A verified 17/20-card hand is the only safe basis for unknown counts.
        # Do not subtract partial or guessed OCR results.
        if status > 0 and self.pending_hand is not None and not self.hand_applied:
            ranks = self.pending_hand
            self.pending_hand = None
            counts = Counter(ranks)
            limits = {'王': 2, **{p.name: 4 for p in templates if p.name != '王'}}
            if len(ranks) in (17, 20) and all(
                name in limits and 0 < count <= limits[name]
                for name, count in counts.items()
            ):
                # Rebuild from a clean deck, then apply the known hand.
                # This is intended for the start of a new round, before any plays.
                for poker in templates:
                    poker.init()
                    poker.num -= counts.get(poker.name, 0)
                self.hand_applied = True
                print('初始手牌已确认：', dict(counts))
            else:
                print('手牌无效：必须输入17或20张，且每个点数不超过牌组数量')
                # A play is accepted only after three identical observations, and
        # only after a blank interval separates it from the previous play.
        if not hasattr(self, '_turn_state'):
            self._turn_state = {key: {'last': None, 'streak': 0, 'latched': False,
                                      'blank': 0} for key in ('upotherList', 'downotherList', 'selfOutList')}
        # Do not reset observation streak on the first active frame.
        for key, cards in (('upotherList', upotherList),
                           ('downotherList', downotherList),
                           ('selfOutList', selfOutList)):
            st = self._turn_state[key]
            # Reject impossible rank multiplicities, including false joker groups.
            valid = bool(cards) and sum(c['num'] for c in cards) <= 20
            if valid:
                valid = all(0 < c['num'] <= (2 if c['name'] == '王' else 4)
                            for c in cards)
            signature = tuple(sorted((c['name'], c['num']) for c in cards)) if valid else None
            if signature is None:
                st['blank'] += 1
                if st['blank'] >= 2:
                    st.update(last=None, streak=0, latched=False)
                continue
            st['blank'] = 0
            if signature == st['last']:
                st['streak'] += 1
            else:
                st['last'] = signature
                st['streak'] = 1
            if st['latched'] or st['streak'] < 3:
                continue
            st['latched'] = True
            # Only subtract if the full observation is physically possible.
            if key != 'selfOutList' and all(
                next((p.num for p in templates if p.name == name), 0) >= count
                for name, count in signature
            ):
                for name, count in signature:
                    next(p for p in templates if p.name == name).num -= count
                outList[key] = cards
            elif key == 'selfOutList':
                outList[key] = cards
        # Rebuild display from the canonical counters after every update.
        selfList = [p.num for p in templates] if status > 0 else []
        self.breakSignal.emit(selfList, handList, outList)

    def run(self):
        while True:
            time.sleep(0.5)
            self.main()


def windowListener():
    global window
    # global logWindow

    window.windowListener()
    # logWindow.windowListener()

def top():
    hwnd = find_game_window()  # 获取当前窗口句柄
    if not hwnd:
        return
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    win32gui.SetForegroundWindow(hwnd)

def main():
    global window
    # global logWindow
    app = QtWidgets.QApplication([])
    if not hWnd:
        print('请先打开微信小程序：腾讯欢乐斗地主')
        return
    window = Window(hWnd)
    # logWindow = LogWindow(hWnd)
    top()

    th1 = MyThread()
    th1.breakSignal.connect(window.setNum)
    window.handConfirmed.connect(th1.set_initial_hand)
    th1.statusSignal.connect(window.setStatus)
    th1.start()
    # window.setStyleSheet('background-color: rgba(0, 0, 0, 0); border-radius:25px; border:2px solid;')

    windowThread = WindowThread()
    windowThread.breakSignal.connect(windowListener)
    windowThread.start()


    window.showWin()
    # logWindow.showWin()

    # window.setNum(1)
    sys.exit(app.exec_())


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
