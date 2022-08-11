from gi.repository import Gtk


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/game_card.ui")
class GameCard(Gtk.Box):
    __gtype_name__ = "GameCard"

    card_image = Gtk.Template.Child()

    def __init__(self, game, path, **kwargs):
        self.game = game
        super().__init__(**kwargs)

        self.card_image.set_filename(path)
