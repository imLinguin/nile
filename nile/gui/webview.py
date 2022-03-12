# import webview
from PyQt5.Qt import QUrl
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage


class LoginWindow:
    def __init__(self, url):
        # self.window = webview.create_window("Login", url=url, height=720, width=450)
        self.page_url = url
        self.window = QWebEngineView()
        self.window.setWindowTitle("Login")
        self.window.setFixedWidth(450)
        self.window.setFixedHeight(750)
        self.window.page().profile().setHttpUserAgent("Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36")
        self.window.load(QUrl(self.page_url))

    def show(self, handler):
        if handler:
            self.window.urlChanged.connect(handler)
        self.window.show()

    def stop(self):
        self.window.hide()
        self.window.close()
