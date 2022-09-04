from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/about_window.ui")
class AboutNile(Adw.AboutWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
