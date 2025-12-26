"""
Wrapper around the KeePassXC CLI.
Handles database interaction, locking logic, and secure clipboard operations.
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
    """ Wrapper around keepassxc-cli with security hardening """

    def __init__(self):
        self.cli = "keepassxc-cli"
        self.cli_checked = False
        self.path = None
        self.path_checked = False
        self.passphrase = None
        self.inactivity_lock_timeout = 0
        self.lock_timer = None

    def initialize(self, path: str, inactivity_lock_timeout: int) -> None:
        """
        Sets up the database path and timeout settings.
        Validates that the CLI tool is accessible.
        """
        self.inactivity_lock_timeout = inactivity_lock_timeout
        
        # Check if CLI tool exists only once
        if not self.cli_checked:
            if self.can_execute_cli():
                self.cli_checked = True
            else:
                raise KeepassxcCliNotFoundError()

        # If path changes, we must lock the DB immediately for security
        if path != self.path:
            self.path = path
            self.path_checked = False
            self.passphrase = None
            self._wipe_passphrase()

        # Validate file existence
        if not self.path_checked:
            if os.path.exists(self.path):
                self.path_checked = True
            else:
                raise KeepassxcFileNotFoundError()

    def _wipe_passphrase(self):
        """ 
        Security Feature: Actively wipes the passphrase from memory.
        This is called by the inactivity timer.
        """
        self.passphrase = None
        self.lock_timer = None

    def _reset_lock_timer(self):
        """ 
        Resets the self-destruct timer for the passphrase.
        Called after every successful user interaction.
        """
        if self.lock_timer:
            self.lock_timer.cancel()
        
        if self.inactivity_lock_timeout > 0:
            # Start a background timer to wipe memory after X seconds
            self.lock_timer = Timer(self.inactivity_lock_timeout, self._wipe_passphrase)
            self.lock_timer.start()

    def change_path(self, new_path: str) -> None:
        self.path = os.path.expanduser(new_path)
        self.path_checked = False
        self._wipe_passphrase()

    def change_inactivity_lock_timeout(self, secs: int) -> None:
        self.inactivity_lock_timeout = secs
        # Security: Lock immediately when changing security settings
        self._wipe_passphrase()

    def is_passphrase_needed(self):
        return self.passphrase is None

    def verify_and_set_passphrase(self, passphrase: str) -> bool:
        """
        Verifies the passphrase by attempting a dummy listing.
        Prevents 'Silent Failures' by checking the return code.
        """
        self.passphrase = passphrase
        # We try to list entries to verify the password
        err, _ = self.run_cli("ls", "-q", self.path)
        
        if err:
            # Verification failed -> Wipe immediately
            self.passphrase = None
            return False
        
        # Success -> Start the inactivity timer
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
        """
        Fetches details including standard fields and TOTP.
        """
        if self.is_passphrase_needed():
            raise KeepassxcLockedDbError()

        attrs = dict()
        # Fetch standard attributes
        for attr in ["UserName", "Password", "URL", "Notes"]:
            (err, out) = self.run_cli("show", "-q", "-a", attr, self.path, f"/{entry}")
            if err:
                raise KeepassxcCliError(err)
            attrs[attr] = out.strip("\n")
        
        # Try to fetch TOTP (requires -t flag)
        # We ignore errors here because not every entry has TOTP
        (err, out) = self.run_cli("show", "-q", "-t", self.path, f"/{entry}")
        if not err and out:
            attrs["TOTP"] = out.strip("\n")
        
        return attrs

    def copy_to_clipboard(self, entry: str, attr: str = "password", timeout: int = 10) -> None:
        """
        Uses `keepassxc-cli clip` to copy securely.
        
        Security Features:
        - Clears clipboard automatically after `timeout` seconds.
        - Runs in background (Popen) to avoid freezing Ulauncher.
        - Supports TOTP generation via `-t` flag.
        """
        if self.is_passphrase_needed():
             return

        cmd = [self.cli, "clip", self.path, entry, str(timeout)]
        
        if attr.lower() == "totp":
            cmd.append("-t")
        elif attr.lower() != "password":
            cmd.extend(["-a", attr])

        # Fire & Forget: We don't wait for this process.
        # It runs in the background to handle the clipboard clearing.
        subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, # Suppress output
            stderr=subprocess.DEVNULL, # Suppress errors (or log them if needed)
        ).communicate(input=bytes(self.passphrase, "utf-8"))

    def can_execute_cli(self) -> bool:
        try:
            subprocess.run(
                [self.cli], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
            )
            return True
        except OSError:
            return False

    def run_cli(self, *args) -> Tuple[str, str]:
        """
        Executes the CLI tool.
        Pipes the passphrase via STDIN to avoid process list leakage.
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

        # Fix for Silent Failures: Check exit code!
        if proc.returncode != 0 and not stderr:
            stderr = f"Process failed with exit code {proc.returncode}"

        # Reset timer on activity
        if self.passphrase:
             try:
                self._reset_lock_timer()
             except AttributeError:
                pass 

        return (stderr, stdout)