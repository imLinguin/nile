import webview


class LoginWindow():
    def __init__(self, url):
        self.window = webview.create_window("Login", url=url, height=720, width=450)

    def show(self, handler):
        self.window.events.loaded += handler
        webview.start(self.window, user_agent="AGSLauncher/1.0.0")

    def get_url(self):
        return self.window.get_current_url()

    def stop(self):
        self.window.hide()
        self.window.destroy()