import sys
from typing import Optional
import PySide6
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Slot, Signal
import spider


class DownloadThread(QtCore.QThread):
    '''
    用来放置下载操作的线程
    '''

    def setting(
        self,
        spider: spider.Spider,
        file_path: str,
        is_append: bool,
        start_chapter: int,
    ) -> None:
        self.spider = spider
        self.file_path = file_path
        self.is_append = is_append
        self.start_chapter = start_chapter

    def run(self) -> None:
        self.spider.save_novel(self.file_path, self.is_append,
                               self.start_chapter)


class NStdout(QtCore.QObject):
    '''
    新的标准输出流，用于将print打印出的信息转向到别的地方
    '''

    msg_comming = Signal(str)

    def write(self, s: str):
        self.msg_comming.emit(s)


class DownloadPage(QtWidgets.QWidget):

    def __init__(
            self,
            parent: Optional[PySide6.QtWidgets.QWidget] = None,
            f: PySide6.QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)
        self.th = DownloadThread()
        self.th.finished.connect(self.save_finished)
        self.nstdout = NStdout()
        self.initUI()

    def initUI(self):
        font = QtGui.QFont('微软雅黑', 10)

        # 小说页面网址输入
        self.label1 = QtWidgets.QLabel()
        self.label1.setFont(font)
        self.label1.setText('小说页面网址')

        self.line1 = QtWidgets.QLineEdit()
        self.line1.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.NoContextMenu)  # 取消右键菜单
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

        # 标准输出流转向
        self.nstdout.msg_comming.connect(self.print_info)
        sys.stdout = self.nstdout
        sys.stderr = self.nstdout

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

    @Slot()
    def save_novel(self):
        '''
        保存小说
        '''
        self.line1.setEnabled(False)
        self.line2.setEnabled(False)
        self.line3.setEnabled(False)
        self.line4.setEnabled(False)
        self.saveBtn.setEnabled(False)
        sp = spider.Spider(self.line2.text(), self.line1.text(),
                           self.line3.text(), self.line4.text())
        file_path = sys.path[0] + '/道诡异仙.txt'
        is_append = False
        start_chapter = 1
        self.th.setting(sp, file_path, is_append, start_chapter)
        self.th.start()

    @Slot(str)
    def print_info(self, s: str):
        '''
        在textedit里打印提示信息

        @param s 新的提示信息
        '''
        self.info.setText(self.info.toPlainText() + s)  # 追加新信息
        self.info.verticalScrollBar().setValue(
            self.info.verticalScrollBar().maximumHeight())  # 将滚条设置到最底下

    @Slot()
    def save_finished(self):
        '''
        保存完毕之后
        '''
        self.line1.setEnabled(True)
        self.line2.setEnabled(True)
        self.line3.setEnabled(True)
        self.line4.setEnabled(True)
        self.saveBtn.setEnabled(True)


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
