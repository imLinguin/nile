import webview


class LoginWindow():
    def __init__(self, url):
        self.window = webview.create_window("Login", url=url, height=720, width=450)

    def show(self, handler):
        self.window.events.loaded += handler
        webview.start(user_agent="Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36")

    def get_url(self):
        return self.window.get_current_url()

    def stop(self):
        self.window.hide()
        self.window.destroy()