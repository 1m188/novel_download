import sys
from typing import Optional
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
import spider


class DownloadPage(QtWidgets.QWidget):

    def __init__(
            self,
            parent: Optional[PySide6.QtWidgets.QWidget] = None,
            f: PySide6.QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)
        self.initUI()

    def initUI(self):
        font = QtGui.QFont('微软雅黑', 10)

        # 小说页面网址输入
        self.label1 = QtWidgets.QLabel()
        self.label1.setFont(font)
        self.label1.setText('小说页面网址')

        self.line1 = QtWidgets.QLineEdit()
        self.line1.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.line1.setFont(font)
        self.line1.setText(spider.URL)

        # 小说网站网址输入
        self.label2 = QtWidgets.QLabel()
        self.label2.setFont(font)
        self.label2.setText('小说网站网址')

        self.line2 = QtWidgets.QLineEdit()
        self.line2.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.line2.setFont(font)
        self.line2.setText(spider.WEBSITE)

        # 网站内容编码
        self.label3 = QtWidgets.QLabel()
        self.label3.setFont(font)
        self.label3.setText('网站内容编码')

        self.line3 = QtWidgets.QLineEdit()
        self.line3.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.line3.setFont(font)
        self.line3.setText(spider.ENCODING)

        # 网站元素解析器
        self.label4 = QtWidgets.QLabel()
        self.label4.setFont(font)
        self.label4.setText('网站元素解析器')

        self.line4 = QtWidgets.QLineEdit()
        self.line4.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.line4.setFont(font)
        self.line4.setText(spider.PARSER)

        # 信息输出
        self.info = QtWidgets.QTextEdit()
        self.info.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.info.setReadOnly(True)
        self.info.setFont(font)

        # 开始缓存按钮
        self.saveBtn = QtWidgets.QPushButton()
        self.saveBtn.setFont(font)
        self.saveBtn.setText('开始缓存')
        self.saveBtn.clicked.connect(self.save_novel)

        # 两两横向布局
        self.hbox1 = QtWidgets.QHBoxLayout()
        self.hbox1.addWidget(self.label1)
        self.hbox1.addWidget(self.line1)

        self.hbox2 = QtWidgets.QHBoxLayout()
        self.hbox2.addWidget(self.label2)
        self.hbox2.addWidget(self.line2)

        self.hbox3 = QtWidgets.QHBoxLayout()
        self.hbox3.addWidget(self.label3)
        self.hbox3.addWidget(self.line3)

        self.hbox4 = QtWidgets.QHBoxLayout()
        self.hbox4.addWidget(self.label4)
        self.hbox4.addWidget(self.line4)

        # 整体布局
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addLayout(self.hbox1, 0, 0, 1, 10)
        self.grid.addLayout(self.hbox2, 1, 0, 1, 10)
        self.grid.addLayout(self.hbox3, 2, 0, 1, 10)
        self.grid.addLayout(self.hbox4, 3, 0, 1, 10)
        self.grid.addWidget(self.info, 4, 0, 4, 10)
        self.grid.addWidget(self.saveBtn, 8, 9, 1, 1)

    @QtCore.Slot()
    def save_novel(self):
        sp = spider.Spider(self.line2.text(), self.line1.text(),
                           self.line3.text(), self.line4.text())
        sp.save_novel(sys.path[0] + '/道诡异仙.txt', False)


class GUI(QtWidgets.QWidget):

    def __init__(
            self,
            parent: Optional[PySide6.QtWidgets.QWidget] = None,
            f: PySide6.QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('novel download')

        self.tab = QtWidgets.QTabWidget()
        self.tab.setFont(QtGui.QFont('微软雅黑', 12))
        self.page = DownloadPage()
        self.tab.addTab(self.page, '手机电子书')

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.tab)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    gui = GUI()
    gui.show()
    sys.exit(app.exec())
