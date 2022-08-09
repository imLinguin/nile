# import webview
from gi.repository import WebKit2, Adw, Gtk


class LoginWindow:
    def __init__(self, url, **kwargs):
        self.page_url = url
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window = Adw.Window(title="Login", modal=False, **kwargs)
        self.window.set_default_size(450, 750)
        self.webview = WebKit2.WebView()

        self.webview.set_vexpand(True)
        box.append(Adw.HeaderBar())
        box.append(self.webview)

        settings = self.webview.get_settings()

        settings.set_user_agent(
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
        )

        self.webview.set_settings(settings)

        self.webview.load_uri(self.page_url)
        self.window.set_content(box)

    def show(self, handler):
        if handler:
            self.webview.connect("load-changed", handler)
        self.window.show()

    def stop(self):
        self.window.close()
