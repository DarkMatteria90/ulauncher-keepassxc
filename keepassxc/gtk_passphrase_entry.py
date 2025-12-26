"""
GTK Window for entering the KeepassXC passphrase.
Includes fixes for UI freezing and double-submission issues.
"""
import gi
gi.require_version("Gtk", "3.0")
# pylint: disable=wrong-import-position
from gi.repository import Gtk, GdkPixbuf

class GtkPassphraseEntryWindow(Gtk.Window):
    """
    A modal window that asks the user for a password.
    """

    def __init__(self, verify_passphrase_fn=None, icon_file=None):
        super(GtkPassphraseEntryWindow, self).__init__(title="Enter passphrase")
        self.verify_passphrase_fn = verify_passphrase_fn
        self.passphrase = None

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)
        self.set_resizable(False)
        self.set_keep_above(True)  # Try to keep on top

        if icon_file:
            self.set_icon(GdkPixbuf.Pixbuf.new_from_file(icon_file))

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.label = Gtk.Label(label="Please enter passphrase to unlock the database:")
        vbox.pack_start(self.label, True, True, 0)

        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)  # Hide characters (Password mode)
        self.entry.connect("activate", self.enter_pressed)
        vbox.pack_start(self.entry, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def read_passphrase(self):
        """
        Starts the GTK main loop and blocks until the window is closed.
        """
        Gtk.main()
        return self.passphrase

    def enter_pressed(self, entry: Gtk.Entry) -> None:
        """
        Handle the Enter key event.
        Includes safeguards against double-submission and UI freezing.
        """
        # Safety: Prevent double-execution if user mashes Enter
        if not self.entry.get_is_focusable() or not self.entry.get_sensitive():
             return 
        
        # Lock input to indicate "Working..."
        self.entry.set_sensitive(False) 

        passphrase = entry.get_text()
        
        if self.verify_passphrase_fn:
            # Update UI to show we are verifying
            self.show_verifying_passphrase()
            
            # This is the blocking call to keepassxc-cli
            if self.verify_passphrase_fn(passphrase):
                self.passphrase = passphrase
                self.close_window()
            else:
                # IMPORTANT: If verification fails, re-enable the input!
                self.entry.set_sensitive(True) 
                self.entry.grab_focus()
                self.show_incorrect_passphrase()
        else:
            # No verification function provided (should not happen in this ext)
            self.passphrase = passphrase
            self.close_window()

    def show_verifying_passphrase(self) -> None:
        """
        Updates label and forces a UI redraw to prevent "frozen" look.
        """
        self.label.set_markup("Verifying passphrase...")
        
        # Force GTK to process pending events (like redrawing the label)
        # BEFORE we block the thread with the CLI call.
        while Gtk.events_pending():
            Gtk.main_iteration()

    def show_incorrect_passphrase(self) -> None:
        """
        Updates label to show error state.
        """
        self.label.set_markup(
            '<span foreground="red">Incorrect passphrase, please try again:</span>'
        )

    def close_window(self) -> None:
        self.destroy()