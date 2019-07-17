#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019-07-08 16:23
# @Author  : Hao
# @Site    : 
# @File    : windowqt.py
# @Software: PyCharm
import sys

# 这里我们提供必要的引用。基本控件位于pyqt5.qtwidgets模块中。
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject,QBasicTimer,QDate,QStringListModel,QModelIndex,QSize
from PyQt5.QtGui import QColor,QIcon,QPixmap
import sip
import requests
from lxml import html
import re
import pyperclip
from goodsItemInfo import *
from ua import *
import random

class Communicate(QObject):
    closeApp = pyqtSignal()

class MYMianWindows(QWidget):
    def __init__(self):
        super().__init__()
        self.initWindows()

    def initWindows(self):
        col = QColor(0, 0, 0)
        self.btn = QPushButton('开始', self)
        self.btn.move(700, 20)
        self.btn.clicked.connect(self.showDialog)

        self.le = QLineEdit("红酒", self)
        self.le.move(20, 20)
        self.le.resize(680, 20)

        self.table = QTableWidget(0, 0)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 50, 10, 10)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.setGeometry(800, 600, 290, 150)
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)


        self.setWindowTitle('京东评价')
        self.resize(800, 600)
        self.show()

    def getHTMLText(self, url):
        try:
            headers = {
                'User-Agent': random.choice(user_agents),
                'authority': 'search.jd.com'
            }
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return r.text
        except Exception as e:
            print(e)
            return ''

    def showDialog(self):
        self.btn.setEnabled(False)
        self.table.clearContents()
        text = self.le.text()
        start_url = 'https://search.jd.com/Search?keyword='+text+'&enc=utf-8'
        res = self.getHTMLText(start_url)
        etree = html.etree
        s = etree.HTML(res)
        items = s.xpath('//ul[@class="J_valueList v-fixed"]//li')

        titlelist = []
        linklist = []

        for item in items:
            name = item.xpath('./a/@title')[0]
            titlelist.append(name.strip())

            url = item.xpath('./a/@href')[0]

            url = url[:7]+"psort=3&"+url[7:]

            linklist.append("https://search.jd.com/"+url.strip())


        self.table.setRowCount(len(titlelist))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['商品名称', 'URL'])
        self.table.setAutoScroll(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # # 允许右键产生菜单
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        # 将右键菜单绑定到槽函数generateMenu
        self.table.customContextMenuRequested.connect(self.generateMenu)

        for i, item in enumerate(zip(titlelist, linklist)):
            newtable = QTableWidgetItem(item[0])
            newtable1 = QTableWidgetItem(item[1])
            self.table.setItem(i, 0, newtable)
            self.table.setItem(i, 1, newtable1)

            searchBtn = QPushButton('执行')
            searchBtn.setStyleSheet('QPushButton{margin:3px}')
            searchBtn.clicked.connect(self.test)
            searchBtn.setProperty('row', str(i))
            self.table.setCellWidget(i, 2, searchBtn)

        self.btn.setEnabled(True)


    def generateMenu(self, pos):
        # 计算有多少条数据，默认-1,
        row_num = -1
        for i in self.table.selectionModel().selection().indexes():
            row_num = i.row()

        # 表格中只有两条有效数据，所以只在前两行支持右键弹出菜单
        if row_num < self.table.rowCount():
            menu = QMenu()
            item1 = menu.addAction(u'复制')

            action = menu.exec_(self.table.mapToGlobal(pos))
            # 显示选中行的数据文本
            if action == item1:
                pyperclip.copy(self.table.item(row_num, 1).text())  # 复制
                print('URL：', self.table.item(row_num, 1).text())



    def test(self,clientid):
        # index = QModelIndex()
        index = self.sender().property("row")

        dialog = goodsItemDialog()
        dialog.setItemUrl(self.table.item(int(index), 1).text())
        dialog.setItemName(self.table.item(int(index), 0).text())
        dialog.show()
        dialog.exec_()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MYMianWindows()
    sys.exit(app.exec_())
