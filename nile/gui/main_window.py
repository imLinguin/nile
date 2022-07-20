from gi.repository import Gtk, GLib, Gio, Adw


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_default_size(1600, 900)
