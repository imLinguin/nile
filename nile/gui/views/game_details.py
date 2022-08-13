import os
from gi.repository import Adw, Gtk, GdkPixbuf
from nile.constants import *


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/game_details.ui")
class GameDetails(Adw.Bin):
    __gtype_name__ = "GameDetails"
    page_background = Gtk.Template.Child()
    page_logo = Gtk.Template.Child()
    game_description = Gtk.Template.Child()
    overview_box = Gtk.Template.Child()

    screenshots_carousel = Gtk.Template.Child()
    screenshot_previous_button = Gtk.Template.Child()
    screenshot_next_button = Gtk.Template.Child()

    genre_detail_entry = Gtk.Template.Child()
    developer_detail_entry = Gtk.Template.Child()
    publisher_detail_entry = Gtk.Template.Child()

    def __init__(self, library_manager, **kwargs):
        super().__init__(**kwargs)
        self.library_manager = library_manager
        self.screenshots = []

        self.screenshot_previous_button.connect("clicked", self.__previous_screnshot)
        self.screenshot_next_button.connect("clicked", self.__next_screnshot)
        self.screenshots_carousel.connect("page-changed", self.__handle_page_change)

    def load_details(self, game):
        self.game = game
        print("Loading", game["product"]["title"])
        # Load images if possible
        background_image_url = game["product"]["productDetail"]["details"].get(
            "backgroundUrl1"
        )
        if not background_image_url:
            background_image_url = game["product"]["productDetail"]["details"].get(
                "backgroundUrl2"
            )

        self.game_description.set_label(
            game["product"]["productDetail"]["details"].get("shortDescription")
        )

        self.genre_detail_entry.set_subtitle(
            ", ".join(game["product"]["productDetail"]["details"].get("genres"))
        )
        self.developer_detail_entry.set_subtitle(
            game["product"]["productDetail"]["details"].get("developer")
        )
        self.publisher_detail_entry.set_subtitle(
            game["product"]["productDetail"]["details"].get("publisher")
        )

        logo_url = game["product"]["productDetail"]["details"]["logoUrl"]

        background_image_path = self.__cache_image(background_image_url)
        logo_path = self.__cache_image(logo_url)

        for screenshot in self.screenshots:
            self.screenshots_carousel.remove(screenshot)

        self.screenshots = []

        for image in game["product"]["productDetail"]["details"].get("screenshots"):
            element = Gtk.Picture()
            element.set_filename(self.__cache_image(image))
            self.screenshots.append(element)
            self.screenshots_carousel.append(element)

        self.page_background.set_pixbuf(self.__load_pixbuf(background_image_path, True))
        self.page_logo.set_pixbuf(self.__load_pixbuf(logo_path))

    def __previous_screnshot(self, widget):
        index = int(self.screenshots_carousel.get_position())
        previous_page = self.screenshots_carousel.get_nth_page(index - 1)
        if previous_page:
            self.screenshots_carousel.scroll_to(previous_page, True)

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
