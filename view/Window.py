#!/usr/bin/python
# coding:utf-8

"""
@author: css
@software: PyCharm
@file: Window.py
@time: 2021/3/3 22:02:25
"""
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon, QFont, QTextCursor
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QSystemTrayIcon, QScrollArea, QTextBrowser, QMenu, QLabel, QAction)
import time
import win32gui, win32con
from util.screen import screen
import cv2 as cv


class Window(QWidget):
    isTopWin = True
    selfWnd = None
    height = 80
    pokerLogStr = ''

    def __init__(self, hWnd):
        super().__init__()
        left, top, right, bot = win32gui.GetWindowRect(hWnd)
        self.setGeometry(0, 0, max(1040, right - left), self.height)
        # Qt.WindowStaysOnTopHint |
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)

        # 任务栏托盘
        # 在系统托盘处显示图标
        self.tp = QSystemTrayIcon(self)
        self.tp.setIcon(QIcon('icon.png'))
        # 设置系统托盘图标的菜单
        a1 = QAction('&欢乐斗地主记牌器', self, triggered=self.showTray)
        a2 = QAction('&退出(Exit)', self, triggered=self.quitApp)  # 直接退出可以用qApp.quit
        tpMenu = QMenu()
        tpMenu.addAction(a1)
        tpMenu.addAction(a2)
        self.tp.setObjectName("记牌器")
        self.tp.setContextMenu(tpMenu)
        # 不调用show不会显示系统托盘
        self.tp.show()
        self.tp.activated.connect(self.act)
        # 信息提示
        # 参数1：标题
        # 参数2：内容
        # 参数3：图标（0没有图标 1信息图标 2警告图标 3错误图标），0还是有一个小图标
        self.tp.showMessage('tp', 'tpContent', icon=0)

        self.hWnd = hWnd
        self.setWindowTitle("CV记牌器")
        # Fixed-width aligned columns: rich-text spaces collapsed and clipped values.
        self.rank_names = ['王','2','A','K','Q','J','10','9','8','7','6','5','4','3']
        self.rank_cells = []
        self.count_cells = []
        QLabel('牌型：', self).setGeometry(0, 0, 70, 26)
        QLabel('数量：', self).setGeometry(0, 26, 70, 26)
        for i, rank in enumerate(self.rank_names):
            x = 70 + i * 43
            rank_label = QLabel(rank, self)
            rank_label.setGeometry(x, 0, 43, 26)
            rank_label.setAlignment(Qt.AlignCenter)
            rank_label.setFont(QtGui.QFont('Microsoft YaHei', 11, QtGui.QFont.Bold))
            count_label = QLabel('?', self)
            count_label.setGeometry(x, 26, 43, 26)
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setFont(QtGui.QFont('Microsoft YaHei', 11, QtGui.QFont.Bold))
            self.rank_cells.append(rank_label)
            self.count_cells.append(count_label)
        self.pokerNumLabel = QLabel(self)
        self.pokerNumLabel.hide()
        self.handlePokerLabel = QLabel(self)
        self.handlePokerLabel.setGeometry(QRect(0, 52, 680, 27))
        self.handlePokerLabel.setFont(QtGui.QFont('Microsoft YaHei', 11, QtGui.QFont.Bold))

        self.screen = QPushButton(self)
        self.screen.setText("截图")
        self.screen.setGeometry(QRect(950, 3, 50, 20))
        self.screen.clicked.connect(self.screenshot)

        self.status = QLabel(self)
        self.status.setGeometry(QRect(230, 58, 80, 20))
        self.status.setText("未开始")
        self.status.setFont(QtGui.QFont("Microsoft YaHei", 11, QtGui.QFont.Bold))
        self.status.setStyleSheet('color: orange')

        self.setPokerSizeLabel = QPushButton(self)
        self.setPokerSizeLabel.setGeometry(QRect(950, 29, 80, 20))
        self.setPokerSizeLabel.setText("调整大小")
        # self.setPokerSizeLabel.setFont(QtGui.QFont("Microsoft YaHei", 11, QtGui.QFont.Bold))
        self.setPokerSizeLabel.clicked.connect(self.setPokerSize)
        self.clearLogButton = QPushButton(self)
        self.clearLogButton.setGeometry(QRect(950, 55, 80, 20))
        self.clearLogButton.setText("清空日志")
        # self.setPokerSizeLabel.setFont(QtGui.QFont("Microsoft YaHei", 11, QtGui.QFont.Bold))
        self.clearLogButton.clicked.connect(self.clearLog)

        line = QLabel(self)
        # 设置标签的左边距，上边距，宽，高
        line.setGeometry(QRect(0, 27, 690, 1))
        line.setAutoFillBackground(True)
        line.setStyleSheet('background-color: rgb(0, 0, 0)')
        line = QLabel(self)
        # 设置标签的左边距，上边距，宽，高
        line.setGeometry(QRect(0, 52, 690, 1))
        line.setAutoFillBackground(True)
        line.setStyleSheet('background-color: rgb(0, 0, 0)')
        line = QLabel(self)
        # 设置标签的左边距，上边距，宽，高
        line.setGeometry(QRect(700, 0, 80, 30))
        line.setAutoFillBackground(True)
        # line.setStyleSheet('background-color: rgb(0, 0, 0)')
        line.setText("出牌\n日志:")
        line = QLabel(self)
        # 设置标签的左边距，上边距，宽，高
        line.setGeometry(QRect(690, 0, 1, self.height))
        line.setAutoFillBackground(True)
        line.setStyleSheet('background-color: rgb(0, 0, 0)')
        for index in range(13):
            line = QLabel(self)
            # 设置标签的左边距，上边距，宽，高
            line.setGeometry(QRect(index * 45 + 113, 0, 1, self.height if index < 3 else 53))
            line.setAutoFillBackground(True)
            line.setStyleSheet('background-color: rgb(0, 0, 0)')
        self.log_text = QTextBrowser(self)
        self.log_text.move(740, 0)
        self.log_text.resize(200, 80)
        self.log_text.setText(self.pokerLogStr)

    def setStatus(self, status):
        if (status == 0):
            self.status.setText("未开始")
            sss = self.getFontLabelText("对局结束", 'red')
            print(sss)
            self.log_text.append(self.getFontLabelText("对局结束", 'red'))
        elif status == 1:
            self.status.setText("开局")
            self.log_text.append(self.getFontLabelText("对局开始", 'green'))
        elif status == 2:
            self.status.setText("进行中")

    def setPokerSize(self):
        left, top, right, bot = win32gui.GetWindowRect(self.hWnd)
        win32gui.SetWindowPos(self.hWnd, None, left, top, 1040, 629, win32con.SWP_SHOWWINDOW)
        self.resize(1040, 80)

    def clearLog(self):
        self.log_text.clear()

    def screenshot(self):
        img = screen(self.hWnd)
        if img is None:
            print('截图失败：请保持游戏窗口可见')
            return
        import os
        os.makedirs('screen', exist_ok=True)
        cv.imwrite('screen/screen' + str(time.time()).split('.')[0] + '.png', img)

    def color(self, num):
        if num == 0:
            return 'black'
        if num == 1:
            return 'green'
        if num == 2:
            return '#66b1ff'
        if num == 3:
            return 'orange'
        if num == 4:
            return 'red'

    def getFontLabelText(self, text, color, font=18):
        return "<font style = 'font-size:" + str(
            font) + "px; font-weight: bold; color:" + color + ";'>" + text + "</font>"

    def setNum(self, num, handNum, outList):
        # Display all 14 ranks in dedicated cells, never using HTML whitespace.
        for i, cell in enumerate(self.count_cells):
            if i < len(num) and isinstance(num[i], (int, float)):
                value = int(num[i])
                cell.setText(str(value))
                cell.setStyleSheet('color: ' + (self.color(value) or 'black'))
            else:
                cell.setText('?')
                cell.setStyleSheet('color: gray')
        self.setHandPokerNum(handNum)
        self.appendPokerLog(outList)

    def appendPokerLog(self, logList):
        list = []
        pokerLogStr = ''
        # print(logList)
        if 'upotherList' in logList:
            pokerLogStr += '上家：'
            list = logList['upotherList']
        if 'downotherList' in logList:
            pokerLogStr += '下家：'
            list = logList['downotherList']
        if 'selfOutList' in logList:
            pokerLogStr += '自家：'
            list = logList['selfOutList']
        if (len(list) > 0):
            list.sort(key=lambda poker: poker['x'])
            for item in list:
                for num in range(0, item['num']):
                    pokerLogStr += item['name']
            self.log_text.append(pokerLogStr)
            self.log_text.moveCursor(self.log_text.textCursor().End)

    def gText(self, text, color='red'):
        return "<font style = 'font-size:16px; font-weight: bold; color:" + color + ";'>" + text + "</font> &nbsp;"

    def setHandPokerNum(self, num):
        text = '底牌：'
        if len(num) > 0:
            text += '&nbsp;'
        for index in num:
            text += self.gText(str(index), 'red')
        self.handlePokerLabel.setText(text)
        # print(num)

    def windowListener(self):
        from util.screen import find_game_window
        hwnd = find_game_window()
        if not hwnd:
            return
        self.hWnd = hwnd
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        fgWnd = win32gui.GetForegroundWindow()

        self.move(left, top - self.height)
        # print(win32gui.GetWindowLong(self.selfWnd, win32con.GWL_EXSTYLE))
        if fgWnd != self.hWnd and fgWnd != self.selfWnd:  # 不是顶层
            if not self.isTopWin:
                # 隐藏
                win32gui.SetWindowPos(self.selfWnd, win32con.HWND_BOTTOM, left, top - self.height, max(1040, right - left),
                                      self.height,
                                      win32con.SWP_SHOWWINDOW)
                self.isTopWin = True
        else:
            if self.isTopWin:
                self.isTopWin = False
                # 置顶
                win32gui.SetWindowPos(self.selfWnd, win32con.HWND_TOPMOST, left, top - self.height, right - left,
                                      self.height,
                                      win32con.SWP_SHOWWINDOW)

    def showTray(self):
        pass

    def quitApp(self):
        QCoreApplication.instance().quit()
        # 在应用程序全部关闭后，TrayIcon其实还不会自动消失，
        # 直到你的鼠标移动到上面去后，才会消失，
        # 这是个问题，（如同你terminate一些带TrayIcon的应用程序时出现的状况），
        # 这种问题的解决我是通过在程序退出前将其setVisible(False)来完成的。
        self.tp.setVisible(False)

    def act(self, reason):
        # 鼠标点击icon传递的信号会带有一个整形的值，1是表示单击右键，2是双击，3是单击左键，4是用鼠标中键点击
        if reason == 2 or reason == 3:
            self.show()
        # print("系统托盘的图标被点击了")

    def showWin(self):
        self.show()
        self.selfWnd = win32gui.FindWindow(None, "CV记牌器")
