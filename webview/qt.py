"""
(C) 2014-2015 Roman Sirokov
Licensed under BSD license

http://github.com/r0x0r/pywebview/
"""

import sys
import os
import logging
import threading
from webview import OPEN_DIALOG, FOLDER_DIALOG, SAVE_DIALOG

logger = logging.getLogger(__name__)


# Try importing Qt4 modules
try:
    from PyQt4 import QtCore
    from PyQt4.QtWebKit import QWebView
    from PyQt4.QtGui import QWidget, QMainWindow, QVBoxLayout, QApplication, QDialog, QFileDialog

    logger.debug("Using Qt4")
except ImportError as e:
    logger.warn("PyQt4 is not found")
    _import_error = True
else:
    _import_error = False


# Try importing Qt5 modules
if _import_error:
    try:
        from PyQt5 import QtCore
        from PyQt5.QtWebKitWidgets import QWebView
        from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QApplication, QFileDialog

        logger.debug("Using Qt5")
    except ImportError as e:
        logger.warn("PyQt5 is not found")
        _import_error = True
    else:
        _import_error = False


if _import_error:
    raise Exception("This module requires PyQt4 or PyQt5 to work under Linux.")


class BrowserView(QMainWindow):
    instance = None
    url_trigger = QtCore.pyqtSignal(str)
    dialog_trigger = QtCore.pyqtSignal(int, str, bool, str)
    destroy_trigger = QtCore.pyqtSignal()

    def __init__(self, title, url, width, height, resizable, fullscreen, min_size):
        super(BrowserView, self).__init__()
        BrowserView.instance = self

        self._file_name_semaphor = threading.Semaphore(0)

        self.resize(width, height)
        self.setWindowTitle(title)

        if not resizable:
            self.setFixedSize(width, height)

        if fullscreen:
            self.showFullScreen()

        self.setMinimumSize(min_size[0], min_size[1])

        self.view = QWebView(self)
        self.view.setContextMenuPolicy(QtCore.Qt.NoContextMenu)  # disable right click context menu
        self.view.setUrl(QtCore.QUrl(url))

        self.setCentralWidget(self.view)
        self.url_trigger.connect(self._handle_load_url)
        self.dialog_trigger.connect(self._handle_file_dialog)
        self.destroy_trigger.connect(self._handle_destroy_window)

        self.move(QApplication.desktop().availableGeometry().center() - self.rect().center())
        self.activateWindow()
        self.raise_()

    def _handle_file_dialog(self, dialog_type, directory, allow_multiple, save_filename):
        if dialog_type == FOLDER_DIALOG:
            self._file_name = QFileDialog.getExistingDirectory(self, 'Open directory', options=QFileDialog.ShowDirsOnly)
        elif dialog_type == OPEN_DIALOG:
            if allow_multiple:
                self._file_name = QFileDialog.getOpenFileNames(self, 'Open files', directory)
            else:
                self._file_name = QFileDialog.getOpenFileName(self, 'Open file', directory)
        elif dialog_type == SAVE_DIALOG:
            if directory:
                save_filename = os.path.join(str(directory), str(save_filename))

            self._file_name = QFileDialog.getSaveFileName(self, 'Save file', save_filename)

        self._file_name_semaphor.release()

    def _handle_load_url(self, url):
        self.view.setUrl(QtCore.QUrl(url))

    def _handle_destroy_window(self):
        self.close()

    def load_url(self, url):
        self.url_trigger.emit(url)

    def create_file_dialog(self, dialog_type, directory, allow_multiple, save_filename):
        self.dialog_trigger.emit(dialog_type, directory, allow_multiple, save_filename)
        self._file_name_semaphor.acquire()

        if dialog_type == FOLDER_DIALOG or not allow_multiple:
            return str(self._file_name)
        elif allow_multiple:
            file_names = map(str, self._file_name)

            if len(file_names) == 1:
                return file_names[0]
            else:
                return file_names
        else:
            return None

    def destroy_(self):
        self.destroy_trigger.emit()



def create_window(title, url, width, height, resizable, fullscreen, min_size):
    """
    Create a WebView window with Qt. Works with both Qt 4.x and 5.x.
    :param title: Window title
    :param url: URL to load
    :param width: Window width
    :param height: Window height
    :param resizable True if window can be resized, False otherwise
    :return:
    """

    app = QApplication([])

    browser = BrowserView(title, url, width, height, resizable, fullscreen, min_size)
    browser.show()
    app.exec_()


def load_url(url):
    if BrowserView.instance is not None:
        BrowserView.instance.load_url(url)
    else:
        raise Exception("Create a web view window first, before invoking this function")


def destroy_window():
    if BrowserView.instance is not None:
        BrowserView.instance.destroy_()
    else:
        raise Exception("Create a web view window first, before invoking this function")


def create_file_dialog(dialog_type, directory, allow_multiple, save_filename):
    if BrowserView.instance is not None:
        return BrowserView.instance.create_file_dialog(dialog_type, directory, allow_multiple, save_filename)
    else:
        raise Exception("Create a web view window first, before invoking this function")