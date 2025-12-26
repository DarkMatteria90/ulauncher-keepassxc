"""
Wrapper around the KeePassXC CLI

Features:
    - Keep track of passphrase unlock and inactivity lock timeouts
    - Search entries
    - Retrieve entry details (username, password, notes, URL)
"""
from typing import List, Dict, Tuple
import subprocess
import os
from datetime import datetime, timedelta
from threading import Timer


class KeepassxcCliNotFoundError(Exception):
    """
    Unable to execute KeePassXC CLI
    """


class KeepassxcFileNotFoundError(Exception):
    """
    Database file not found on the given path
    """


class KeepassxcLockedDbError(Exception):
    """
    Attempting to access locked database
    """


class KeepassxcCliError(Exception):
    """ Contains error message returned by keepassxc-cli """

    def __init__(self, message):
        super(KeepassxcCliError, self).__init__()
        self.message = message


class KeepassxcDatabase:
    """ Wrapper around keepassxc-cli with ACTUAL security """

    def __init__(self):
        self.cli = "keepassxc-cli"
        self.cli_checked = False
        self.path = None
        self.path_checked = False
        self.passphrase = None
        self.inactivity_lock_timeout = 0
        self.lock_timer = None 

    def _wipe_passphrase(self):
        """ Nuke it from orbit. """
        self.passphrase = None
        self.lock_timer = None

    def _reset_lock_timer(self):
        """ Resets the self-destruct timer """
        if self.lock_timer:
            self.lock_timer.cancel()
        
        if self.inactivity_lock_timeout > 0:
            # Start a background thread to clean up
            self.lock_timer = Timer(self.inactivity_lock_timeout, self._wipe_passphrase)
            self.lock_timer.start()

    def change_inactivity_lock_timeout(self, secs: int) -> None:
        self.inactivity_lock_timeout = secs
        self._wipe_passphrase() # lock instant when config changes

    def is_passphrase_needed(self):
        return self.passphrase is None

    def verify_and_set_passphrase(self, passphrase: str) -> bool:
        self.passphrase = passphrase
        err, _ = self.run_cli("ls", "-q", self.path)
        if err:
            self.passphrase = None
            return False
        
        # Pw is correct, start timer
        self._reset_lock_timer()
        return True

def run_cli(self, *args) -> Tuple[str, str]:
        """
        Execute the KeePassXC CLI with given args, parse output and handle errors
        """
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

        if self.inactivity_lock_timeout and self.passphrase:

             pass 
             

        if self.passphrase:
            try:
                self._reset_lock_timer()
            except AttributeError:
                pass 

        return (stderr, stdout)
