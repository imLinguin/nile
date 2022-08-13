from gettext import gettext as _
import logging
from threading import Thread
from gi.repository import Gtk, GLib, Gio, Adw

import time

from nile.gui.views.library import Library
from nile.gui.views.loading import LoadingPage
from nile.gui.views.game_details import GameDetails
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
    back_button = Gtk.Template.Child()
    toasts = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self.logger = logging.getLogger("MAIN_WINDOW")
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
        self.game_details_view = GameDetails(self.library_manager)

        self.main_stack.add_named(name="loading", child=self.loading_view)
        self.main_stack.add_named(name="library", child=self.library_view)
        self.main_stack.add_named(name="details", child=self.game_details_view)
        self.logger.info("Registered stack")
        self.main_stack.connect(
            "notify::visible-child", self.__handle_stack_page_change
        )
        self.search_button.connect("clicked", self.library_view.open_search)
        self.back_button.connect("clicked", self.__open_library_page)

        Thread(target=self.initialize).start()
        if not self.authorization_handler.is_logged_in():
            self.show_onboard()

    def initialize(self):
        if not self.authorization_handler.is_logged_in():
            return
        self.logger.info("Initializing")
        if self.authorization_handler.is_token_expired():
            self.authorization_handler.refresh_token()

        if self.config_handler.get("library"):
            self.library_manager.sync()

        self.library_manager.pull_games_tumbnails()

        self.library_view.render()

        if self.header_bar.has_css_class("flat"):
            self.header_bar.remove_css_class("flat")
        self.main_stack.set_visible_child_name("library")
        user_name = self.config_handler.get(
            "user", "extensions//customer_info//given_name"
        )
        welcome_back_message = _("Welcome back")
        self.toasts.add_toast(
            Adw.Toast(title=f"{welcome_back_message} {user_name}!", timeout=5)
        )

    def show_onboard(self):
        self.logger.info("Spawning onboard")
        self.onboard_window = OnBoard(self)
        self.onboard_window.present()

    def open_login_page(self, event):
        self.logger.info("Spawning login window")
        url, handler = self.authorization_handler.login()
        self.login_window = LoginWindow(url)
        self.login_window.window.connect("close-request", self.__handle_login_abort)
        self.login_window.show(
            lambda webview, event: self.__handle_login(handler, webview, event)
        )
        if self.onboard_window:
            self.onboard_window.hide()

    def sync_games(self):
        self.logger.info("Synchonizing game library")
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
        self.back_button.set_visible(name == "details")

    def __handle_login(self, handler, webview, event):
        res = handler(webview, event)
        if res and self.onboard_window:
            self.login_window.stop()
            self.onboard_window.present()
            self.onboard_window.next_page()

    def __open_library_page(self, widget):
        self.game_details_view.set_visible_child_name("loading")
        self.main_stack.set_visible_child_name("library")

    def open_game_details(self, game):
        self.main_stack.set_visible_child_name("details")
        Thread(target=self.game_details_view.load_details, args=[game]).start()
