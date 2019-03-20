"""GUI dialog for reporting issues"""
import os
import json
from gi.repository import Gtk
from lutris.gui.dialogs import NoticeDialog
from lutris.util.graphics import drivers
from lutris.util.graphics.glxinfo import GlxInfo
from lutris.util.linux import LINUX_SYSTEM

def gather_system_info():
    """Get all system information in a single data structure"""
    system_info = {}
    if drivers.is_nvidia:
        system_info["nvidia_driver"] = drivers.get_nvidia_driver_info()
        system_info["nvidia_gpus"] = [
            drivers.get_nvidia_gpu_info(gpu_id)
            for gpu_id in drivers.get_nvidia_gpu_ids()
        ]
    system_info["gpus"] = [drivers.get_gpu_info(gpu) for gpu in drivers.get_gpus()]
    system_info["env"] = dict(os.environ)
    system_info["missing_libs"] = LINUX_SYSTEM.get_missing_libs()
    system_info["cpus"] = LINUX_SYSTEM.get_cpus()
    system_info["drives"] = LINUX_SYSTEM.get_drives()
    system_info["ram"] = LINUX_SYSTEM.get_ram_info()
    system_info["dist"] = LINUX_SYSTEM.get_dist_info()
    system_info["glxinfo"] = GlxInfo().as_dict()
    return system_info


class BaseApplicationWindow(Gtk.ApplicationWindow):
    """Window used to guide the user through a issue reporting process"""
    def __init__(self, application):
        Gtk.ApplicationWindow.__init__(self, icon_name="lutris", application=application)
        self.application = application
        self.set_show_menubar(False)
        self.set_size_request(420, 420)
        self.set_default_size(600, 480)
        self.set_position(Gtk.WindowPosition.CENTER)


        self.vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            visible=True
        )
        self.vbox.set_margin_top(18)
        self.vbox.set_margin_bottom(18)
        self.vbox.set_margin_right(18)
        self.vbox.set_margin_left(18)
        self.add(self.vbox)
        self.action_buttons = Gtk.Box(spacing=6)
        self.vbox.pack_end(self.action_buttons, False, False, 0)

    def get_action_button(self, label, handler=None, tooltip=None):
        """Returns a button that can be used for the action bar"""
        button = Gtk.Button.new_with_mnemonic(label)
        if handler:
            button.connect("clicked", handler)
        if tooltip:
            button.set_tooltip_text(tooltip)
        return button

    def on_destroy(self, _widget=None):
        self.destroy()


class IssueReportWindow(BaseApplicationWindow):
    def __init__(self, application):
        super().__init__(application)


        # Title label
        self.title_label = Gtk.Label(visible=True)
        self.vbox.add(self.title_label)

        title_label = Gtk.Label()
        title_label.set_markup("<b>Submit an issue</b>")
        self.vbox.add(title_label)
        self.vbox.add(Gtk.HSeparator())

        issue_entry_label = Gtk.Label(
            "Describe the problem you're having in the text box below. "
            "This information will be sent the Lutris team along with your system information."
            "You can also save this information locally if you are offline."
        )
        issue_entry_label.set_max_width_chars(80)
        issue_entry_label.set_property("wrap", True)
        self.vbox.add(issue_entry_label)

        self.textview = Gtk.TextView()
        self.textview.set_pixels_above_lines(12)
        self.textview.set_pixels_below_lines(12)
        self.textview.set_left_margin(12)
        self.textview.set_right_margin(12)
        self.vbox.pack_start(self.textview, True, True, 0)

        self.action_buttons = Gtk.Box(spacing=6)
        action_buttons_alignment = Gtk.Alignment.new(1, 0, 0, 0)
        action_buttons_alignment.add(self.action_buttons)
        self.vbox.pack_start(action_buttons_alignment, False, True, 0)

        cancel_button = self.get_action_button(
            "C_ancel",
            handler=self.on_destroy
        )
        self.action_buttons.add(cancel_button)

        save_button = self.get_action_button(
            "_Save",
            handler=self.on_save
        )
        self.action_buttons.add(save_button)

        self.show_all()

    def get_issue_info(self):
        buffer = self.textview.get_buffer()
        return {
            'comment': buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True),
            'system': gather_system_info()
        }

    def on_save(self, _button):
        """Signal handler for the save button"""

        save_dialog = Gtk.FileChooserDialog(
            title="Select a location to save the issue",
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=("_Cancel", Gtk.ResponseType.CLOSE, "_OK", Gtk.ResponseType.OK),
        )
        save_dialog.connect("response", self.on_folder_selected)
        save_dialog.run()

    def on_folder_selected(self, dialog, response):
        if response != Gtk.ResponseType.OK:
            return
        target_path = dialog.get_current_folder()
        if not target_path:
            return
        issue_path = os.path.join(target_path, "lutris-issue-report.json")
        issue_info = self.get_issue_info()
        with open(issue_path, "w") as issue_file:
            json.dump(issue_info, issue_file, indent=2)
        dialog.destroy()
        NoticeDialog("Issue saved in %s" % issue_path)
