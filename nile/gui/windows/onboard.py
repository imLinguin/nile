from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/onboard.ui")
class OnBoard(Adw.Window):
    __gtype_name__ = "OnBoard"

    carousel = Gtk.Template.Child()
    login_button = Gtk.Template.Child()
    next_page_button = Gtk.Template.Child()
    sync_games_button = Gtk.Template.Child()
    sync_spinner = Gtk.Template.Child()
    close_modal = Gtk.Template.Child()

    def __init__(self, main_window, **kwargs):
        super().__init__(parent=main_window, **kwargs)
        self.main_window = main_window

        self.login_button.connect("clicked", main_window.open_login_page)
        self.next_page_button.connect("clicked", self.next_page)
        self.sync_games_button.connect("clicked", self.__sync_games)
        self.close_modal.connect("clicked", self.__close)
        self.carousel.connect("page-changed", self.handle_page_change)

    def handle_page_change(
        self,
        widget,
        index,
    ):
        number_of_pages = widget.get_n_pages()
        self.next_page_button.set_visible(index + 1 < number_of_pages)

    def __sync_games(self, widget):
        self.sync_games_button.set_visible(False)
        self.sync_spinner.start()
        self.main_window.sync_games()

    def previous_page(self, widget=None):
        index = int(self.carousel.get_position())
        previous_page = self.carousel.get_nth_page(index - 1)
        if previous_page:
            self.carousel.scroll_to(previous_page, True)

    def next_page(self, widget=None):
        index = int(self.carousel.get_position())
        next_page = self.carousel.get_nth_page(index + 1)
        if next_page:
            self.carousel.scroll_to(next_page, True)

    def __close(self, widget):
        self.main_window.initialize()
        self.destroy()
