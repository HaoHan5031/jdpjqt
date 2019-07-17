#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019-07-11 15:12
# @Author  : Hao
# @Site    : 
# @File    : goodsItemInfo.py
# @Software: PyCharm
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject,QBasicTimer,QDate,QStringListModel,QModelIndex,QSize,QRect
from PyQt5.QtGui import QColor,QIcon,QPixmap, QBrush
import sip
import requests
from lxml import html
import asyncio
from pyppeteer import launch
import random
from goodsinfomodel import *
from aiohttp import ClientSession
import re
import pprint
import json
import platform
from ua import *

headers = {'User-Agent': random.choice(user_agents), 'Referer':''}

async def main(url):
    sysstr = platform.system()
    if (sysstr == "Windows"):
        apppath = ""
    else:
        apppath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    browser = await launch({
        "headless": True,
        # 重新指定临时数据路径，解决windows系统 OSError: Unable to remove Temporary User Data报错问题
        "executablePath": apppath,
        # 有头的不要加这句话，容易导致浏览器进程无法结束
        "args": ['--no-sandbox'],
        'dumpio': True})  # "dumpio": True 解决浏览器卡住问题
    """浏览器启动的时候，自动使用cookies信息或者缓存填写了账号输入框，通过系新建上下文，可以解决多个浏览器数据共享的问题，暂时没想到其他的解决方案"""
    context = await browser.createIncognitoBrowserContext()
    page = await context.newPage()
    # page = await browser.newPage() # 启动个新的浏览器页面
    # 新定义的注入js函数每次导航或者加载新的页面时会自动执行js注入 比起page.evaluate()每打开一个页面都要单独注入一次好用
    await inject_js(page)
    await page.setUserAgent(
        random.choice(user_agents))

    # goto到指定网页并且等到网络空闲为止
    await page.goto(url, {"waitUntil": 'networkidle2'})

    await get_cookie(page)


    # 滚动到页面底部
    await page.evaluate('window.scrollBy(0, document.body.scrollHeight)')

    await asyncio.sleep(1)

    etree = html.etree
    s = etree.HTML(await page.content())
    items = s.xpath('//div[@class="gl-i-wrap"]')
    itemlist = []

    for item in items:
        model = goodsinfomodel()
        try:
            imageurl = item.xpath('./div[@class="p-img"]//a/img/@src')[0]
        except Exception as e:
            imageurl = item.xpath('./div[@class="p-img"]//a/img/@data-lazy-img')[0]
        name = item.xpath('./div[@class="p-img"]//a/@title')[0]
        itemurl = 'https:' + item.xpath('./div[@class="p-img"]//a/@href')[0]
        price = item.xpath('./div[@class="p-price"]//i/text()')[0]
        count = item.xpath('./div[@class="p-commit"]//a/text()')[0]

        model.imageUrl = "https:" + imageurl
        model.name = name
        model.price = price
        model.pjcount = count
        model.itemUrl = itemurl
        itemlist.append(model)

    await browser.close()
    return itemlist



async def get_cookie(page):
    cookies_list = await page.cookies()
    cookies = ""
    for cookie in cookies_list:
        str_cookie = "{0}={1};"
        str_cookie = str_cookie.format(cookie["name"], cookie["value"])
        cookies += str_cookie
    # print(cookies)
    return cookies


def input_time_random():
    return random.randint(100, 151)


async def inject_js(page):
    js1 = "() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => undefined } }) }"
    js2 = "() =>{ window.navigator.chrome = { runtime: {},  }; }"
    js3 = "() =>{ Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); }"
    js4 = "() =>{ Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5,6], }); }"
    await page.evaluateOnNewDocument(js1)
    await page.evaluateOnNewDocument(js2)
    await page.evaluateOnNewDocument(js3)
    await page.evaluateOnNewDocument(js4)

tasks = []


async def getpj(url):
    headers["Referer"] = url
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.read()

async def updatepj(url, data):
    async with ClientSession() as session:
        async with session.post(url, data=data) as response:
            return await response.text(encoding="utf-8")


class goodsItemDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(700)
        self.setMinimumSize(QSize(800, 600))
        # self.setStyleSheet("background-color: red;")

        self.btn = QPushButton('开始', self)
        self.btn.move(700, 20)
        self.btn.clicked.connect(self.getItems)

        self.lab = QLabel("haha", self)
        self.lab.move(10, 10)

        self.le = QLineEdit(self)
        self.le.move(10, 50)
        self.resize(100, 20)

        # self.labUrl = QLabel("haha", self)
        # self.labUrl.move(10, 30)
        #
        # self.labUrl.setGeometry(QRect(10, 30, 680, 27 * 4)) # 四倍行距
        # self.labUrl.setWordWrap(True)
        # self.labUrl.setAlignment(Qt.AlignTop)

        self.itemUrl = ""
        self.itemName = ""

        self.itemlist = []

        self.table = QTableWidget(0, 0)
        self.tablepj = QTableWidget(1, 1)
        self.tablepj.setColumnCount(1)

        self.tablepj.setHorizontalHeaderLabels(['评价'])
        self.tablepj.setAutoScroll(True)
        self.tablepj.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tablepj.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.table.setWordWrap(True)
        # self.table.resizeRowsToContents()
        self.tablepj.resizeColumnsToContents()
        # # 允许右键产生菜单
        self.tablepj.setContextMenuPolicy(Qt.CustomContextMenu)
        # 将右键菜单绑定到槽函数generateMenu
        self.tablepj.customContextMenuRequested.connect(self.generateMenu)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 100, 10, 10)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.table)

        hlayout = QVBoxLayout()
        hlayout.addWidget(self.tablepj)

        layout.addLayout(vlayout)
        layout.addLayout(hlayout)
        layout.setStretch(0, 2)
        layout.setStretch(1, 1)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.itemlist = []

    def setItemUrl(self, url):
        self.itemUrl = url
        # self.labUrl.setText(url)


    def setItemName(self, name):
        self.itemName = name
        self.lab.setText(name)

    def getItems(self):
        self.btn.setEnabled(False)
        loop = asyncio.get_event_loop()
        self.itemlist = loop.run_until_complete(main(self.itemUrl))
        self.start()

    def start(self):
        self.table.clearContents()
        self.table.setColumnCount(5)
        self.table.setRowCount(len(self.itemlist))
        self.table.setHorizontalHeaderLabels(['图片', '名称', '价格', '评价数', '执行'])
        self.table.setAutoScroll(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.table.setWordWrap(True)
        # self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()


        # # 允许右键产生菜单
        # self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        # # 将右键菜单绑定到槽函数generateMenu
        # self.table.customContextMenuRequested.connect(self.generateMenu)

        for i, item in enumerate(self.itemlist):
            newtable = QTableWidgetItem(item.name)
            newtable.setToolTip(item.name)
            newtable1 = QTableWidgetItem(item.price)
            newtable1.setTextAlignment(Qt.AlignCenter)
            newtable2 = QTableWidgetItem(item.pjcount)
            newtable2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, newtable)
            self.table.setItem(i, 2, newtable1)
            self.table.setItem(i, 3, newtable2)

            searchBtn = QPushButton('执行')
            searchBtn.setStyleSheet('QPushButton{margin:3px}')
            searchBtn.clicked.connect(self.test)
            searchBtn.setProperty('row', str(i))
            self.table.setCellWidget(i, 4, searchBtn)
            req = requests.get(item.imageUrl)
            photo = QPixmap()
            photo.loadFromData(req.content)
            label = QLabel("1111")
            label.setAlignment(Qt.AlignCenter)  # 水平居中

            # 不要使用背景透明的图片，否则多图层层叠显示
            label.setPixmap(photo.scaled(80, 80))  # 只有图片
            self.table.setCellWidget(i, 0, label)  # self → Ui_form
            self.table.setColumnWidth(1, 200)
            self.table.setRowHeight(i, 120)
        self.btn.setEnabled(True)

    def test(self):
        index = self.sender().property("row")
        item = self.itemlist[int(index)]
        num = re.findall('\d+', str(item.itemUrl))

        for k in range(1, 4):
            strurl = 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv2652&productId=%s&score=0&sortType=5&page=%d&pageSize=10&isShadowSku=0&rid=0&fold=1' % (
                num[0], k)
            task = asyncio.ensure_future(getpj(strurl))
            tasks.append(task)

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(asyncio.gather(*tasks))

        # result = result.decode(result.encoding)

        def rep(x):
            x = str(x, encoding='gbk')
            return x

        res = list(map(rep, result))

        def rep1(x):
            x = x[x.find("(") + 1:x.rfind(")")]
            x = x.replace(":", "")
            x = x.replace('"', "")
            x = x.replace(',', '')
            x = x.replace('\\n','')
            return x

        res1 = list(map(rep1, res))
        pjList = []
        def rep2(x):
            lista = re.findall("content(.*?.)creationTime", x)
            return lista

        listall = list(map(rep2, res1))
        for item in listall:
            pjList.extend(item)

        # pprint.pprint(pjList[0:len(pjList):2])
        setItem = set(pjList)
        self.tablepj.clearContents()
        self.tablepj.setRowCount(len(setItem))

        index = 0
        for i, item in enumerate(setItem):
            if item:
                item = item.replace("京东", "懒猪")
                item = item.replace("jd", "懒猪")
                newtable = QTableWidgetItem(item)
                newtable.setToolTip(item)
                self.tablepj.setItem(index, 0, newtable)
                self.tablepj.setRowHeight(index, 120)
                index += 1


    def generateMenu(self, pos):
        # 计算有多少条数据，默认-1,
        row_num = -1
        tasks = []
        goodsid = self.le.text()
        for i in self.tablepj.selectionModel().selection().indexes():
            row_num = i.row()

        # 表格中只有两条有效数据，所以只在前两行支持右键弹出菜单
        if row_num < self.tablepj.rowCount():
            menu = QMenu()
            item1 = menu.addAction(u'上传')

            action = menu.exec_(self.tablepj.mapToGlobal(pos))
            # 显示选中行的数据文本
            if action == item1:
                content = self.tablepj.item(row_num, 0).text()

                data = {"goods_id": goodsid, "content": content}
                task = asyncio.ensure_future(updatepj("http://shop.uiomall.com/api/Index/add_goods_comment", data))
                tasks.append(task)
        if row_num != -1 and goodsid != "":
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(asyncio.gather(*tasks))
            dictR = json.loads(result[0])
            if dictR["code"] == 1:
                self.tablepj.item(row_num, 0).setForeground(QBrush(QColor(255, 0, 0)))
                QMessageBox.question(self, '提示', '上传评论成功', QMessageBox.Yes)
            else:
                QMessageBox.question(self, '提示', '上传失败请检查商品id是否正确', QMessageBox.Yes)
        else:
            QMessageBox.question(self, '提示', '请填写商品id', QMessageBox.Yes)


