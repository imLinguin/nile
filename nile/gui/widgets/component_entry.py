import subprocess
from threading import Thread
from gi.repository import Gtk, Adw
from nile.constants import *
import os

@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/component_entry.ui")
class ComponentEntry(Adw.ActionRow):
    __gtype_name__ = "ComponentEntry"

    delete_button = Gtk.Template.Child()
    browse_files = Gtk.Template.Child()
    install_button  = Gtk.Template.Child()

    percentage_label = Gtk.Template.Child()

    def __init__(self, data, wine_manager, **kwargs):
        super().__init__(**kwargs)
        self.wine_manager = wine_manager
        self.data = data
        self.set_title(data["name"])

        self.install_button.connect("clicked", self.download)
        self.browse_files.connect("clicked", self.open_folder)

    def download(self, widget):
        manifest = self.wine_manager.get_component_manifest(self.data["name"], self.data["Category"], self.data.get("Sub-category"))

        Thread(target=self.wine_manager.download_component, args=(manifest, self.data, self.get_percentage, self.finished)).start()
        self.install_button.set_visible(False)
        self.percentage_label.set_visible(True)


    def open_folder(self, widget):
        arg = os.path.join(DATA_PATH, "components", self.data["Category"], self.data["Sub-category"] if self.data.get("Sub-category") else "", self.data["name"])        

        subprocess.run(["xdg-open",  arg])

    def finished(self, success):
        if not success:
            return
        self.browse_files.set_visible(True)
        self.percentage_label.set_visible(False)

    def get_percentage(self, percentage):
        self.percentage_label.set_label(f"{percentage}%")

    def set_existing(self, value):
        if value:
            self.install_button.set_visible(False)
            self.browse_files.set_visible(True)
        else:
            self.browse_files.set_visible(False)
            self.install_button.set_visible(True)