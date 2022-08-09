from gettext import gettext as t
from gi.repository import Gtk, GLib, Gio, Adw
from nile.gui.views.library import Library
from nile.gui.windows.onboard import OnBoard
from nile.gui.windows.webview import LoginWindow
from nile.utils.config import Config
from nile.api.library import Library as LibraryManager
from nile.api.authorization import AuthenticationManager
from nile.api.session import APIHandler

from threading import Thread


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/main.ui")
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "NileWindow"
    main_stack = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self.config_handler = Config()
        self.session_manager = APIHandler()
        self.library_manager = LibraryManager(self.config_handler, self.session_manager)
        self.authorization_handler = AuthenticationManager(
            self.session_manager, self.config_handler, self.library_manager
        )
        super().__init__(**kwargs)
        self.present()
        self.__start()

    def __start(self):
        user_credentials = self.config_handler.get("user")
        self.library_view = Library(self.library_manager)

        self.main_stack.add_titled(
            name="library", child=self.library_view, title=t("Library")
        )
        if not user_credentials.get("tokens"):
            self.show_onboard()

    def show_onboard(self):
        self.onboard_window = OnBoard(self)
        self.onboard_window.present()

    def open_login_page(self, event):
        print("Open", event)
        url, handler = self.authorization_handler.login()
        self.login_window = LoginWindow(url)
        self.login_window.window.connect("close-request", self.__handle_login_abort)
        self.login_window.show(
            lambda webview, event: self.__handle_login(handler, webview, event)
        )
        if self.onboard_window:
            self.onboard_window.hide()

    def sync_games(self):
        sync_thread = Thread(target=self.__handle_library_sync)
        sync_thread.start()

    def __handle_library_sync(self):
        self.library_manager.sync()
        self.onboard_window.next_page()

    def __handle_login_abort(self, window):
        if self.onboard_window:
            self.onboard_window.present()

        return False

    def __handle_login(self, handler, webview, event):
        res = handler(webview, event)
        if res and self.onboard_window:
            self.login_window.stop()
            self.onboard_window.present()
            self.onboard_window.next_page()
