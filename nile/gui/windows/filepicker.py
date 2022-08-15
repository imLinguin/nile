from gi.repository import Gtk


class FilePicker:
    def __init__(self, title, parent, action, callback, *buttons, native=True):

        if native:
            dialog = Gtk.FileChooserNative.new(title, parent, action, *buttons)

        else:
            dialog = Gtk.FileChooserDialog(
                title=title,
                action=action,
            )
            dialog.add_buttons(*buttons)
            dialog.set_transient_for(parent)

        dialog.connect("response", callback, dialog)

        dialog.set_modal(True)
        dialog.show()
