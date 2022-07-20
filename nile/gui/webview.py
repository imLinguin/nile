# import webview
from gi.repository import WebKit2, Adw


class LoginWindow:
    def __init__(self, url, **kwargs):
        self.page_url = url
        self.window = Adw.ApplicationWindow(title="Login", **kwargs)
        self.window.set_default_size(450, 750)
        self.webview = WebKit2.WebView()

        settings = self.webview.get_settings()

        settings.set_user_agent(
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
        )

        self.webview.set_settings(settings)

        self.webview.load_uri(self.page_url)

        self.window.set_content(self.webview)

    def show(self, handler):
        if handler:
            self.webview.do_load_changed = handler
        self.window.show()

    def stop(self):
        self.window.hide()
        self.window.close()
