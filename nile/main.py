import sys
import logging
import gi
import gettext

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit2", "5.0")

from gi.repository import Gtk, Adw, Gio, GObject

from nile.gui.windows.webview import LoginWindow


gettext.bindtextdomain("nile")
gettext.textdomain("nile")


class Nile(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.imLinguin.nile", register_session=True
        )
        logging.basicConfig(
            level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s"
        )
        self.headless = False
        self.spawn_login = (False, "", None)
        self.window = None

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.__register_actions()

    def do_activate(self):
        from nile.gui.windows.main_window import MainWindow

        if self.headless:
            if self.spawn_login[0]:
                self.webview = LoginWindow(self.spawn_login[1], application=self)
                self.webview.show(self.spawn_login[2])
            return
        window = self.props.active_window
        if not window:
            window = MainWindow(application=self)

        self.window = window
        window.present()

    def do_command_line(self, command):

        self.do_activate()
        return 0

    def __quit(self, x, y):
        quit()

    def __register_actions(self):

        actions = [
            ("quit", self.__quit, ("app.quit", ["<Ctrl>Q"])),
        ]

        for action, callback, accel in actions:
            simple_action = Gio.SimpleAction.new(action, None)
            simple_action.connect("activate", callback)
            self.add_action(simple_action)
            if accel is not None:
                self.set_accels_for_action(*accel)


def main(version):
    app = Nile()

    sys.exit(app.run())
