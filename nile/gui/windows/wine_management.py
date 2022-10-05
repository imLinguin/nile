from gi.repository import Adw, Gtk, GLib

from nile.gui.widgets.component_entry import ComponentEntry;

@Gtk.Template(resource_path="/io/github/imLinguin/nile/gui/ui/wine_management.ui")
class NileWineMgmt(Adw.Window):
    __gtype_name__ = "NileWineMgmt"

    wine_ge_row = Gtk.Template.Child()
    soda_row = Gtk.Template.Child()
    caffe_row = Gtk.Template.Child()
    lutris_row = Gtk.Template.Child()
    lutris_ge_row = Gtk.Template.Child()

    dxvk_row = Gtk.Template.Child()
    vkd3d_row = Gtk.Template.Child()


    def __init__(self, wine_manager, **kwargs):
        super().__init__(**kwargs)
        self.wine_manager = wine_manager

        self.rows_by_name = dict()
        self.parse_index_file()
    
    def parse_index_file(self):
        
        
        components_object = self.wine_manager.read_components()

        existing_keys = self.wine_manager.get_existing_components_list(components_object)

        wine_builds, dxvk, vkd3d = self.filter_components(components_object)

        wine_ge_builds = self.filter_array(lambda x: x["name"].startswith("wine-ge-"), wine_builds)
        soda_builds = self.filter_array(lambda x: x["name"].startswith("soda-"), wine_builds)
        caffe_builds = self.filter_array(lambda x: x["name"].startswith("caffe-"), wine_builds) 
        lutris_builds = self.filter_array(lambda x: x["name"].startswith("lutris") and not "ge" in x["name"], wine_builds)
        lutris_builds_ge = self.filter_array(lambda x: x["name"].startswith("lutris") and "ge" in x["name"], wine_builds)

        for build in wine_ge_builds:
            self.rows_by_name[build["name"]] = ComponentEntry(build, self.wine_manager)
            self.wine_ge_row.add_row(self.rows_by_name[build["name"]])

        for build in soda_builds:
            self.rows_by_name[build["name"]] = ComponentEntry(build, self.wine_manager)
            self.soda_row.add_row(self.rows_by_name[build["name"]])

        for build in caffe_builds:
            self.rows_by_name[build["name"]] = ComponentEntry(build, self.wine_manager)
            self.caffe_row.add_row(self.rows_by_name[build["name"]])

        for build in lutris_builds:
            self.rows_by_name[build["name"]] = ComponentEntry(build, self.wine_manager)
            self.lutris_row.add_row(self.rows_by_name[build["name"]])

        for build in lutris_builds_ge:
            self.rows_by_name[build["name"]] = ComponentEntry(build, self.wine_manager)
            self.lutris_ge_row.add_row(self.rows_by_name[build["name"]])

        for build in dxvk:
            self.rows_by_name[build["name"]] = ComponentEntry(build, self.wine_manager)
            self.dxvk_row.add_row(self.rows_by_name[build["name"]])

        for build in vkd3d:
            self.rows_by_name[build["name"]] = ComponentEntry(build, self.wine_manager)
            self.vkd3d_row.add_row(self.rows_by_name[build["name"]])

        for row in self.rows_by_name.values():
            if row.data["name"] in existing_keys:
                GLib.idle_add(row.set_existing, True)

    def filter_array(self, function, array):
        output = list()

        for object in array:
            if function(object):
                output.append(object)
        return output

    def filter_components(self, components):
        dxvk = list()
        wine_builds = list()
        vkd3d = list()
        for key in components.keys():
            if components[key].get('Sub-category') == 'wine':
                components[key]["name"] = key
                wine_builds.append(components[key])
            elif components[key]["Category"] == 'dxvk' and not "async" in key:
                components[key]["name"] = key
                dxvk.append(components[key])
            elif components[key]["Category"] == 'vkd3d':
                components[key]["name"] = key
                vkd3d.append(components[key])

        return wine_builds, dxvk, vkd3d

    