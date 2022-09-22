import os
from threading import Thread
from gettext import gettext as _
from gi.repository import Adw, Gtk
from nile.gui.windows.filepicker import FilePicker
import nile.utils.download as dl_utils
from nile.constants import *


@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/install_game.ui")
class GameInstallModal(Adw.Window):
    __gtype_name__ = "GameInstallModal"

    cancel_button = Gtk.Template.Child()
    install_button = Gtk.Template.Child()
    install_location_select = Gtk.Template.Child()
    install_location = Gtk.Template.Child()

    stack_view = Gtk.Template.Child()

    location_error_image = Gtk.Template.Child()

    install_size = Gtk.Template.Child()

    def __init__(self, callback, game, download_manager, **kwargs):
        super().__init__(**kwargs)

        self.game = game
        self.download_manager = download_manager

        self.patchmanifest = None

        self.init_install = callback

        self.install_location.set_text(DEFAULT_INSTALL_PATH)
        self.cancel_button.connect("clicked", self.__close_window)
        self.install_button.connect("clicked", self.__init_install)
        self.install_location_select.connect("clicked", self.__get_install_folder)
        self.install_location.connect("changed", self.__install_location_changed)

        Thread(target=self.__get_download_patchmanifest).start()
        self.handle_update()

    def __init_install(self, widget):
        Thread(
            target=self.init_install,
            args=[
                os.path.join(
                    self.install_location.get_text().strip(), self.folder_name
                ),
                self.patchmanifest,
            ],
        ).start()
        self.destroy()

    def __get_download_patchmanifest(self):
        comparison, self.folder_name = self.download_manager.init_download(
            self.game, path_folder_name_only=True
        )

        self.patchmanifest = self.download_manager.get_patchmanifest(comparison)

        total_size = sum(f.download_size for f in self.patchmanifest.files)
        size, label = dl_utils.get_readable_size(total_size)

        self.install_size.set_subtitle("{:.2f} {}".format(size, label))
        self.stack_view.set_visible_child_name("content")
        self.handle_update()

    def __install_location_changed(self, widget):
        self.handle_update()

    def __get_install_folder(self, widget):
        FilePicker(
            _("Select installation directory"),
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            self.callback,
            _("Open"),
            native=True,
        )

    def handle_update(self):
        checks = [self.verify_path_correctness(), bool(self.patchmanifest)]

        self.install_button.set_sensitive(not False in checks)

    def verify_path_correctness(self):
        path = self.install_location.get_text()
        self.location_error_image.set_visible(not os.path.exists(path))
        return os.path.exists(path)

    def callback(self, widget, status, path):
        if status == Gtk.ResponseType.ACCEPT:
            selected_file = widget.get_file()
            path = selected_file.get_path()
            if path.startswith("/run/user"):
                self.install_location.set_text(path)
                self.location_error_image.set_visible(True)
                return
            self.install_location.set_text(path)
            self.handle_update()

    def __close_window(self, widget):
        self.destroy()
