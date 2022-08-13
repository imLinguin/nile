from gi.repository import Gtk, GdkPixbuf


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/game_card.ui")
class GameCard(Gtk.Box):
    __gtype_name__ = "GameCard"

    card_image = Gtk.Template.Child()
    click_gesture = Gtk.Template.Child()

    def __init__(self, game, path, **kwargs):
        self.game = game
        super().__init__(**kwargs)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

        self.card_image.set_pixbuf(pixbuf)

        self.click_gesture.connect("pressed", self.__handle_press)

    def __handle_press(self, widget, n, x, y):
        Gtk.Window.get_toplevels()[0].open_game_details(
            self.game
        )  # Refer to window and open game details
