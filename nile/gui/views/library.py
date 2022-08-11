from gi.repository import Gtk, GLib, Gio, Adw
from nile.gui.widgets.game_card import GameCard
from nile.utils.search import calculate_distance
from nile.constants import *


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/library.ui")
class Library(Adw.Bin):
    __gtype_name__ = "NileLibrary"

    library_grid = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()

    def __init__(self, config_manager, library_manager, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = config_manager
        self.library_manager = library_manager

        self.search_entry.connect("changed", self.__handle_search)
        self.library_grid.set_sort_func(self.__sort_func)

    def render(self):
        games = self.config_manager.get("library")
        if not games:
            return
        self.available_genres = []
        for game in games:
            image_path = self.library_manager.get_game_image_fs_path(
                game["product"]["id"]
            )

            card = GameCard(game, image_path)
            self.library_grid.append(card)

            for genre in game["product"]["productDetail"]["details"]["genres"]:
                if not genre in self.available_genres:
                    self.available_genres.append(genre)

    def open_search(self, widget):
        self.search_bar.set_search_mode(not self.search_bar.get_search_mode())

    def __filter_func(self, widget, data):
        title = widget.get_child().game["product"].get("title")
        keywords = (
            widget.get_child()
            .game["product"]["productDetail"]["details"]
            .get("keywords")
        )
        if not data:
            return True

        return data.strip().lower() in title.lower() or self.__search_in_keywords(
            data.strip().lower(), keywords
        )

    def __search_in_keywords(self, query, keywords):
        if not keywords:
            return False
        for keword in keywords:
            if query in keword.lower():
                return True

    def __sort_func(self, widget1, widget2):
        title1 = self.get_element_title(widget1.get_child().game)
        title2 = self.get_element_title(widget2.get_child().game)

        return title1.lower() > title2.lower()

    def __handle_search(self, widget):
        self.library_grid.set_filter_func(self.__filter_func, widget.get_text())

    def get_element_title(self, element):
        return (
            element["product"].get("title")
            if element["product"].get("title") is not None
            else ""
        )
