"""
Wrapper around the KeePassXC CLI
"""
from typing import List, Dict, Tuple
import subprocess
import os
from threading import Timer

class KeepassxcCliNotFoundError(Exception):
    """ Unable to execute KeePassXC CLI """

class KeepassxcFileNotFoundError(Exception):
    """ Database file not found on the given path """

class KeepassxcLockedDbError(Exception):
    """ Attempting to access locked database """

class KeepassxcCliError(Exception):
    """ Contains error message returned by keepassxc-cli """
    def __init__(self, message):
        super(KeepassxcCliError, self).__init__()
        self.message = message

class KeepassxcDatabase:
    """ Wrapper around keepassxc-cli """

    def __init__(self):
        self.cli = "keepassxc-cli"
        self.cli_checked = False
        self.path = None
        self.path_checked = False
        self.passphrase = None
        self.inactivity_lock_timeout = 0
        self.lock_timer = None

    def initialize(self, path: str, inactivity_lock_timeout: int) -> None:
        self.inactivity_lock_timeout = inactivity_lock_timeout
        if not self.cli_checked:
            if self.can_execute_cli():
                self.cli_checked = True
            else:
                raise KeepassxcCliNotFoundError()

        if path != self.path:
            self.path = path
            self.path_checked = False
            self.passphrase = None
            self._wipe_passphrase()

        if not self.path_checked:
            if os.path.exists(self.path):
                self.path_checked = True
            else:
                raise KeepassxcFileNotFoundError()

    def _wipe_passphrase(self):
        """ Nuke it from orbit. """
        self.passphrase = None
        self.lock_timer = None

    def _reset_lock_timer(self):
        """ Resets the self-destruct timer """
        if self.lock_timer:
            self.lock_timer.cancel()
        
        if self.inactivity_lock_timeout > 0:
            self.lock_timer = Timer(self.inactivity_lock_timeout, self._wipe_passphrase)
            self.lock_timer.start()

    def change_path(self, new_path: str) -> None:
        self.path = os.path.expanduser(new_path)
        self.path_checked = False
        self._wipe_passphrase()

    def change_inactivity_lock_timeout(self, secs: int) -> None:
        self.inactivity_lock_timeout = secs
        self._wipe_passphrase()

    def is_passphrase_needed(self):
        return self.passphrase is None

    def verify_and_set_passphrase(self, passphrase: str) -> bool:
        self.passphrase = passphrase
        # Wir rufen run_cli auf, um zu testen. Wenn das hier fehlschlägt, ist das PW falsch.
        err, _ = self.run_cli("ls", "-q", self.path)
        
        if err:
            self.passphrase = None
            return False
        
        self._reset_lock_timer()
        return True

    def search(self, query: str) -> List[str]:
        if self.is_passphrase_needed():
            raise KeepassxcLockedDbError()

        (err, out) = self.run_cli("search", "-q", self.path, query)
        if err:
            if "No results for that" in err:
                return []
            raise KeepassxcCliError(err)
        return [l[1:] for l in out.splitlines()]

    def get_entry_details(self, entry: str) -> Dict[str, str]:
        if self.is_passphrase_needed():
            raise KeepassxcLockedDbError()

        attrs = dict()
        for attr in ["UserName", "Password", "URL", "Notes"]:
            (err, out) = self.run_cli("show", "-q", "-a", attr, self.path, f"/{entry}")
            if err:
                raise KeepassxcCliError(err)
            attrs[attr] = out.strip("\n")
        return attrs

    def can_execute_cli(self) -> bool:
        try:
            subprocess.run(
                [self.cli], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
            )
            return True
        except OSError:
            return False

    def run_cli(self, *args) -> Tuple[str, str]:
        try:
            proc = subprocess.run(
                [self.cli, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                input=bytes(self.passphrase, "utf-8") if self.passphrase else None,
                check=False,
            )
        except OSError:
            raise KeepassxcCliNotFoundError()

        stderr = proc.stderr.decode("utf-8")
        stdout = proc.stdout.decode("utf-8")

        if proc.returncode != 0 and not stderr:
            stderr = f"Process failed with exit code {proc.returncode}"

        if self.passphrase:
             try:
                self._reset_lock_timer()
             except AttributeError:
                pass 

        return (stderr, stdout)
    
    def copy_to_clipboard(self, entry: str, attr: str = "password", timeout: int = 10) -> None:
        """
        Uses keepassxc-cli clip to copy securely and clear after timeout.
        Runs in background (Popen) so we don't freeze the UI.
        """
        if self.is_passphrase_needed():
             # Sollte eigentlich nicht passieren, da wir vorher prüfen,
             # aber sicher ist sicher.
             return

        cmd = [self.cli, "clip", self.path, entry, str(timeout)]
        
        # Wenn es nicht das Passwort ist, müssen wir das Attribut angeben
        if attr.lower() != "password":
            cmd.extend(["-a", attr])

        # Wir feuern den Prozess ab und vergessen ihn (Fire & Forget).
        # keepassxc-cli kümmert sich um das Warten und Löschen.
        subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, # Wir wollen keinen Output
            stderr=subprocess.DEVNULL, 
        ).communicate(input=bytes(self.passphrase, "utf-8"))