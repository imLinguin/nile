from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/loading.ui")
class LoadingPage(Adw.Bin):
    __gtype_name__ = "LoadingPage"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
