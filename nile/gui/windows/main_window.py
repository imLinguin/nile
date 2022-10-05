from gettext import gettext as _
import logging
from threading import Thread
from gi.repository import Gtk, GLib, Adw, GObject

from nile.gui.views.library import Library
from nile.gui.views.loading import LoadingPage
from nile.gui.views.game_details import GameDetails
from nile.gui.windows.onboard import OnBoard
from nile.gui.windows.webview import LoginWindow
from nile.gui.windows.wine_management import NileWineMgmt
from nile.utils.config import Config

from nile.api.library import Library as LibraryManager
from nile.api.authorization import AuthenticationManager
from nile.api.session import APIHandler
from nile.api.graphql import GraphQLHandler
from nile.api.wine import WineManager
from nile.downloading.manager import DownloadManager
from nile.constants import *


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/main.ui")
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "NileWindow"
    main_stack = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    main_leaflet = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    toasts = Gtk.Template.Child()

    about_button = Gtk.Template.Child()
    wine_management_button = Gtk.Template.Child()

    installed_filter_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        self.logger = logging.getLogger("MAIN_WINDOW")
        self.config_handler = Config()
        self.graphql_handler = GraphQLHandler(self.config_handler)
        self.session_manager = APIHandler()
        self.library_manager = LibraryManager(self.config_handler, self.session_manager)
        self.authorization_handler = AuthenticationManager(
            self.session_manager, self.config_handler, self.library_manager
        )
        self.download_manager = DownloadManager(
            self.config_handler, self.library_manager, self.session_manager
        )
        self.wine_manager = WineManager(self.config_handler)


        super().__init__(**kwargs)

        self.connect("close-request", self.__on_close_request)
        self.about_button.connect("clicked", self.__open_about_window)
        if os.environ.get("NILE_DEVEL") == "1":
            self.add_css_class("devel")
        self.present()
        self.__start()

    def __start(self):
        user_credentials = self.config_handler.get("user")
        games = self.config_handler.get("library")

        self.loading_view = LoadingPage()
        self.library_view = Library(self.config_handler, self.library_manager)
        self.library_view.search_bar.set_key_capture_widget(self)
        self.search_button.bind_property(
            "active",
            self.library_view.search_bar,
            "search-mode-enabled",
            GObject.BindingFlags.BIDIRECTIONAL,
        )
        self.game_details_view = GameDetails(
            self,
            self.library_manager,
            self.config_handler,
            self.graphql_handler,
            self.download_manager,
        )

        self.main_stack.add_named(name="loading", child=self.loading_view)
        self.main_stack.add_named(name="library", child=self.library_view)


        self.main_leaflet.append(self.game_details_view)
        self.installed_filter_button.connect("toggled", self.library_view.switch_installed_filter)
        self.wine_management_button.connect("clicked", self.spawn_wine_management)
        self.main_leaflet.connect("notify::visible-child", self.__handle_navigation)
        self.logger.info("Registered stack")

        if not self.authorization_handler.is_logged_in():
            self.show_onboard()
            return


        Thread(target=self.initialize).start()


    def initialize(self):
        self.logger.info("Initializing")
        if self.authorization_handler.is_token_expired():
            self.authorization_handler.refresh_token()

        self.wine_manager.get_repository_index()
        if self.config_handler.get("library"):
            self.library_manager.sync()

        self.library_manager.pull_games_tumbnails()

        self.library_view.render()
        GLib.idle_add(self.__initialize_styles)
        
        user_name = self.config_handler.get(
            "user", "extensions//customer_info//given_name"
        )
        welcome_back_message = _("Welcome back")
        toast = Adw.Toast(title=f"{welcome_back_message} {user_name}!", timeout=5)

        GLib.idle_add(self.toasts.add_toast, toast)

    def __initialize_styles(self):
        if self.header_bar.has_css_class("flat"):
            self.header_bar.remove_css_class("flat")
        self.main_stack.set_visible_child_name("library")
        self.search_button.set_visible(True)
        self.installed_filter_button.set_visible(True)

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
        GLib.idle_add(self.__handle_library_sync)

    def __on_close_request(self, widget):
        return self.download_manager.installing[0]

    def __handle_library_sync(self):
        self.library_manager.sync()
        self.library_view.render()
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

    def __handle_navigation(self, widget, child):
        visible_child = widget.get_visible_child()
        if type(visible_child) == GameDetails:
            if not self.game_details_view.is_loading:
                self.game_details_view.stack.set_visible_child_name("content")
        else:
            self.game_details_view.stack.set_visible_child_name("loading")

    def __open_about_window(self, widget):
        builder = Gtk.Builder.new_from_resource(
            "/io/github/imLinguin/nile/gui/ui/about_window.ui"
        )
        about_window = builder.get_object("about_window")

        about_window.set_transient_for(self)
        about_window.present()

    def spawn_wine_management(self, widget):
        window = NileWineMgmt(self.wine_manager)

        window.set_transient_for(self)
        window.show()

    def open_library_page(self, widget):
        self.main_leaflet.navigate(Adw.NavigationDirection.BACK)

    def open_game_details(self, game):
        if self.authorization_handler.is_token_expired():
            self.authorization_handler.refresh_token()
        Thread(target=self.game_details_view.load_details,args=[game]).start()
        self.main_leaflet.set_visible_child(self.game_details_view)
        self.main_leaflet.set_can_navigate_forward(True)
