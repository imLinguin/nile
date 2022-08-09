from gi.repository import Gtk, GLib, Gio, Adw


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/library.ui")
class Library(Adw.Bin):
    __gtype_name__ = "NileLibrary"

    def __init__(self, library_manager, **kwargs):
        super().__init__(**kwargs)
        self.library_manager = library_manager
