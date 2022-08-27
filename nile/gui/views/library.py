from gi.repository import Gtk, GLib, Gio, Adw
from nile.gui.widgets.game_card import GameCard
from nile.utils.search import calculate_distance
from nile.constants import *
import enum


class FilterType(enum.Enum):
    INSTALLED = 0
    GENRE = 1


class Filter:
    def __init__(self, filter_type: FilterType, value):
        self.type = filter_type
        self.value = value


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/library.ui")
class Library(Adw.Bin):
    __gtype_name__ = "NileLibrary"

    library_grid = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()

    no_results_found_page = Gtk.Template.Child()
    results_stack = Gtk.Template.Child()

    installed_games_filter = Gtk.Template.Child()

    def __init__(self, config_manager, library_manager, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = config_manager
        self.library_manager = library_manager
        self.search_bar.set_key_capture_widget(self)
        self.search_entry.connect("changed", self.__handle_search)
        self.library_grid.connect("child-activated", self.__open_game_details)
        self.installed_games_filter.connect("clicked", self.__switch_installed_filter)
        self.library_grid.set_sort_func(self.__sort_func)
        self.library_grid.set_filter_func(self.__filter_func)

        self.filters = []
        self.grid_entries = []

        self.get_installed_games()

    def render(self):
        games = self.config_manager.get("library")
        self.get_installed_games()
        if not games:
            return
        self.available_genres = []

        for card in self.grid_entries:
            self.library_grid.remove(card)

        for game in games:
            image_path = self.library_manager.get_game_image_fs_path(
                game["product"]["id"]
            )

            card = GameCard(game, image_path)
            self.library_grid.append(card)
            self.grid_entries.append(card)

            for genre in game["product"]["productDetail"]["details"]["genres"]:
                if not genre in self.available_genres:
                    self.available_genres.append(genre)

    def open_search(self, widget):
        self.search_bar.set_search_mode(not self.search_bar.get_search_mode())

    def get_installed_games(self):
        self.installed_games = self.config_manager.get("installed")
        self.installed_ids = [game["id"] for game in self.installed_games]

    def __filter_func(self, widget):
        query = self.search_entry.get_text()
        title = widget.get_child().game["product"].get("title")
        keywords = (
            widget.get_child()
            .game["product"]["productDetail"]["details"]
            .get("keywords")
        )
        if not query:
            game_data = widget.get_child().game

            for filter in self.filters:
                if filter.type == FilterType.INSTALLED:
                    return game_data["product"]["id"] in self.installed_ids

            return True

        shown = query.strip().lower() in title.lower() or self.__search_in_keywords(
            query.strip().lower(), keywords
        )

        return shown

    def __open_game_details(self, widget, target):
        Gtk.Window.get_toplevels()[0].open_game_details(target.get_child().game)

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
        self.library_grid.invalidate_filter()

    def __switch_installed_filter(self, widget):
        if self.installed_games_filter.has_css_class("accent"):
            self.installed_games_filter.remove_css_class("accent")
            filter = None
            for f in self.filters:
                if f.type == FilterType.INSTALLED:
                    filter = f
                    break
            self.filters.remove(filter)
        else:
            self.installed_games_filter.add_css_class("accent")
            self.filters.append(Filter(FilterType.INSTALLED, True))
        self.library_grid.invalidate_filter()

    def get_element_title(self, element):
        return (
            element["product"].get("title")
            if element["product"].get("title") is not None
            else ""
        )
