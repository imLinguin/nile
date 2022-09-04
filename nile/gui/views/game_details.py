import os
from gettext import gettext as _
import datetime
from threading import Thread
from gi.repository import Gtk, GdkPixbuf, GLib
from nile.constants import *
from nile.gui.windows.install_game import GameInstallModal
from nile.downloading.manager import DownloadManagerEvent
from nile.utils.uninstall import uninstall

install_button_text = _("Install")
play_button_text = _("Play")


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/game_details.ui")
class GameDetails(Gtk.Box):
    __gtype_name__ = "GameDetails"
    page_background = Gtk.Template.Child()
    page_logo = Gtk.Template.Child()
    game_description = Gtk.Template.Child()
    overview_box = Gtk.Template.Child()
    scrolled_view = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    screenshots_carousel = Gtk.Template.Child()
    screenshot_previous_button = Gtk.Template.Child()
    screenshot_next_button = Gtk.Template.Child()
    uninstall_button = Gtk.Template.Child()

    genre_detail_entry = Gtk.Template.Child()
    developer_detail_entry = Gtk.Template.Child()
    publisher_detail_entry = Gtk.Template.Child()
    gamemodes_detail_entry = Gtk.Template.Child()
    releasedate_detail_entry = Gtk.Template.Child()

    primary_button = Gtk.Template.Child()
    install_progress = Gtk.Template.Child()

    header_bar = Gtk.Template.Child()
    page_title = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    def __init__(
        self,
        main_window,
        library_manager,
        config_manager,
        graphql_handler,
        download_manager,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.main_window = main_window
        self.library_manager = library_manager
        self.graphql_handler = graphql_handler
        self.config_manager = config_manager
        self.download_manager = download_manager

        self.download_manager.listen(self.__handle_download_manager_event)
        self.screenshots = []
        self.is_installed = False
        self.is_loading = False
        self.screenshot_previous_button.connect("clicked", self.__previous_screnshot)
        self.screenshot_next_button.connect("clicked", self.__next_screnshot)
        self.primary_button.connect("clicked", self.run_primary_action)
        self.back_button.connect("clicked", self.main_window.open_library_page)
        self.uninstall_button.connect("clicked", self.__uninstall_game)
        self.screenshots_carousel.connect("page-changed", self.__handle_page_change)

    def load_details(self, game):
        self.is_loading = True
        self.game = game
        self.is_installed = False
        self.get_installed()

        self.primary_button.set_label(install_button_text)
        self.install_progress.set_visible(False)
        game_product_id = self.game["product"]["id"]
        for installed_game in self.installed:
            if installed_game["id"] == game_product_id:
                self.is_installed = True
                self.primary_button.set_label(play_button_text)
                break

        self.scrolled_view.set_vadjustment(
            self.scrolled_view.get_vadjustment().set_value(0)
        )
        title = game["product"].get("title")
        self.page_title.set_subtitle(title)

        # Load images if possible

        data = self.graphql_handler.get_game_details(game["product"]["id"])
        self.game_data = data

        title = data["data"]["agaGames"][0].get("title")
        self.page_title.set_subtitle(title)
        self.game_description.set_label(data["data"]["agaGames"][0]["description"])

        self.genre_detail_entry.set_subtitle(
            ", ".join(data["data"]["agaGames"][0]["genres"])
        )
        self.developer_detail_entry.set_subtitle(
            data["data"]["agaGames"][0]["developerName"]
        )
        self.publisher_detail_entry.set_subtitle(
            data["data"]["agaGames"][0]["publisher"]
        )
        self.gamemodes_detail_entry.set_subtitle(
            ", ".join(data["data"]["agaGames"][0]["gameModes"])
        )

        self.releasedate_detail_entry.set_subtitle(
            datetime.datetime.fromisoformat(
                data["data"]["agaGames"][0]["releaseDate"][:-1]
            ).strftime("%x")
        )

        background_image_url = data["data"]["agaGames"][0]["background"][
            "defaultMedia"
        ]["src1x"]
        logo_url = data["data"]["agaGames"][0]["logoImage"]["defaultMedia"]["src1x"]

        background_image_path = self.__cache_image(background_image_url)
        logo_path = self.__cache_image(logo_url)

        for screenshot in self.screenshots:
            self.screenshots_carousel.remove(screenshot)

        self.screenshots = []

        self.page_background.set_pixbuf(self.__load_pixbuf(background_image_path, True))
        self.page_logo.set_pixbuf(self.__load_pixbuf(logo_path))
        self.stack.set_visible_child_name("content")
        self.is_loading = False
        Thread(target=self.__fetch_screenshots).start()

    def get_installed(self):
        self.installed = self.config_manager.get("installed")
        if not self.installed:
            self.installed = []

    def run_primary_action(self, widget):
        if not self.is_installed:
            self.__spawn_download_window()

    def __handle_download_manager_event(self, event_type, message):
        if event_type == DownloadManagerEvent.INSTALL_BEGAN:
            self.install_progress.set_visible(True)
            self.primary_button.set_sensitive(False)
        if event_type == DownloadManagerEvent.INSTALL_COMPLETED:
            Thread(target=self.main_window.library_view.render).start()
            self.install_progress.set_visible(False)
            self.get_installed()
            for installed_game in self.installed:
                if installed_game["id"] == self.game["product"]["id"]:
                    self.is_installed = True
                    self.primary_button.set_label(play_button_text)
                    break
            self.primary_button.set_sensitive(True)
        elif event_type == DownloadManagerEvent.INSTALL_PROGRESS:
            if self.download_manager.installing[1] == self.game["product"]["id"]:
                self.install_progress.set_visible(True)
                self.install_progress.set_fraction(message)

    def init_download(self, path, patchmanifest):
        self.primary_button.set_sensitive(False)

        self.download_manager.download_from_patchmanifest(path, patchmanifest)

        self.primary_button.set_sensitive(True)

    def __uninstall_game(self, widget):
        uninstall(self.game["product"]["id"], self.config_manager)

        self.get_installed()
        self.is_installed = False
        self.primary_button.set_label(install_button_text)
        for installed_game in self.installed:
            if installed_game["id"] == self.game["product"]["id"]:
                self.is_installed = True
                self.primary_button.set_label(play_button_text)
                break
        self.main_window.library_view.render()
        self.main_window.library_view.library_grid.invalidate_filter()

    def __spawn_download_window(self):
        self.install_modal = GameInstallModal(
            self.init_download, self.game, self.download_manager
        )
        self.install_modal.set_transient_for(self.main_window)
        self.install_modal.present()

    def __previous_screnshot(self, widget):
        index = int(self.screenshots_carousel.get_position())
        previous_page = self.screenshots_carousel.get_nth_page(index - 1)
        if previous_page:
            self.screenshots_carousel.scroll_to(previous_page, True)

    def __fetch_screenshots(self):
        for image in self.game_data["data"]["agaGames"][0]["screenshots"]:
            element = Gtk.Picture()
            element.add_css_class("game-card")
            element.set_filename(self.__cache_image(image["src1x"]))
            self.screenshots.append(element)
            self.screenshots_carousel.append(element)

    def __next_screnshot(self, widget):
        index = int(self.screenshots_carousel.get_position())
        next_page = self.screenshots_carousel.get_nth_page(index + 1)
        if next_page:
            self.screenshots_carousel.scroll_to(next_page, True)

    def __handle_page_change(self, widget, index):
        self.screenshot_previous_button.set_visible(index > 0)
        self.screenshot_next_button.set_visible(index < widget.get_n_pages() - 1)

    def __cache_image(self, url):
        file_name = url.split("/")[-1]
        file_path = os.path.join(
            CACHE_PATH, "game_images", self.game["product"]["id"], file_name
        )
        os.makedirs(os.path.split(file_path)[0], exist_ok=True)
        if not os.path.exists(file_path):
            data = self.library_manager.fetch_thumbnail(url)
            f = open(file_path, "wb")
            f.write(data)
            f.flush()
            f.close()
        return file_path

    def __load_pixbuf(self, path, crop_height=False):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

        if crop_height:
            return self.__ensure_size(pixbuf, 0, 440)
        else:
            return pixbuf

    def __ensure_size(self, pixbuf, width=0, height=0):
        image_size = pixbuf.get_width(), pixbuf.get_height()

        return pixbuf.new_subpixbuf(
            0,
            0,
            width if width > 0 else image_size[0],
            height if height > 0 else image_size[1],
        )
