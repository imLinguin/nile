from gettext import gettext as t
import logging
from threading import Thread
from gi.repository import Gtk, GLib, Gio, Adw

import time

from nile.gui.views.library import Library
from nile.gui.views.loading import LoadingPage
from nile.gui.windows.onboard import OnBoard
from nile.gui.windows.webview import LoginWindow
from nile.utils.config import Config
from nile.api.library import Library as LibraryManager
from nile.api.authorization import AuthenticationManager
from nile.api.session import APIHandler


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/main.ui")
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "NileWindow"
    main_stack = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    toasts = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self.logger = logging
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
        games = self.config_handler.get("library")

        self.loading_view = LoadingPage()
        self.library_view = Library(self.config_handler, self.library_manager)

        self.main_stack.add_named(name="loading", child=self.loading_view)
        self.main_stack.add_named(name="library", child=self.library_view)

        self.main_stack.connect(
            "notify::visible-child", self.__handle_stack_page_change
        )
        self.search_button.connect("clicked", self.library_view.open_search)

        Thread(target=self.initialize).start()
        if not self.authorization_handler.is_logged_in():
            self.show_onboard()
        else:
            self.library_view.render()

    def initialize(self):
        if self.authorization_handler.is_token_expired():
            self.authorization_handler.refresh_token()
        if not self.config_handler.get("library"):
            self.library_manager.sync()

        thumbnails_fetch_thread = Thread(
            target=self.library_manager.pull_games_tumbnails
        )
        thumbnails_fetch_thread.start()

        thumbnails_fetch_thread.join()
        time.sleep(3)
        self.main_stack.set_visible_child_name("library")
        user_name = self.config_handler.get(
            "user", "extensions//customer_info//given_name"
        )
        self.toasts.add_toast(Adw.Toast(title=f"Welcome back {user_name}!", timeout=5))

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
        self.library_view.render()
        self.onboard_window.next_page()

    def __handle_login_abort(self, window):
        if self.onboard_window:
            self.onboard_window.present()

        return False

    def __handle_stack_page_change(self, widget, child):
        name = self.main_stack.get_visible_child_name()
        self.search_button.set_visible(name == "library")

    def __handle_login(self, handler, webview, event):
        res = handler(webview, event)
        if res and self.onboard_window:
            self.login_window.stop()
            self.onboard_window.present()
            self.onboard_window.next_page()
