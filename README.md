# ulauncher-keepassxc (Modernized & Hardened)

A **Ulauncher** extension to search your **KeePassXC** password manager database.

> ⚠️ **Note:** This is a heavily modernized fork of the original extension. It focuses on **security, stability, and advanced automation features** like Autotype and TOTP support. It fixes long-standing issues like silent failures and insecure memory handling.

## ✨ Features

### 🚀 Automation & Productivity
* **Autotype Support:** Types your credentials directly into the previous window using `xdotool`.
  * Supports: **Password**, **Username**, **URL**, and **TOTP**.
  * *Security:* Keystrokes are piped via STDIN to prevent leakage in process lists (`ps aux`).
* **TOTP Support:** Displays, copies, and types Time-based One-Time Passwords directly from Ulauncher.
* **Smart Actions:** Separate actions for "Type" (Autotype) and "Copy" (Clipboard) for granular control.

### 🛡️ Security & Hardening
* **Secure Clipboard:** Uses `keepassxc-cli clip` to copy passwords.
  * The clipboard is **automatically cleared** by the KeePassXC process after a timeout (default: 10s).
  * No sensitive data remains in your clipboard history manager.
* **Active Memory Wiper:** Passwords are actively wiped from RAM when the inactivity timer expires, rather than relying on Python's garbage collector.
* **Robust Window Handling:** Replaces flaky "sleep timers" with an active polling mechanism to ensure the passphrase window actually receives focus.

## 📦 Requirements

To use the full feature set (especially Autotype and Secure Clipboard), you need the following system packages installed.

| Package | Reason | Command (Debian/Ubuntu) |
| :--- | :--- | :--- |
| **KeePassXC** | The core application (v2.7+ recommended). | `sudo apt install keepassxc` |
| **wmctrl** | Required to bring the passphrase prompt to the foreground. | `sudo apt install wmctrl` |
| **xdotool** | **Required for Autotype** (simulates keystrokes). | `sudo apt install xdotool` |
| **xclip** (or `xsel`) | **Required for Secure Clipboard** (clearing). | `sudo apt install xclip` |

## 🔧 Installation

1.  Open Ulauncher preferences window.
2.  Go to **Extensions** -> **"Add extension"**.
3.  Paste the URL of this repository:
    ```
    [(https://github.com/DarkMatteria90/ulauncher-keepassxc/)]
    ```

## ⚙️ Configuration

| Preference | Description | Default |
| :--- | :--- | :--- |
| **Password database location** | Path to your `.kdbx` file. | - |
| **Inactivity lock timeout** | Time in seconds before the extension locks and **wipes the passphrase from memory**. Set to `0` to disable (not recommended). | `600` (10 min) |
| **Max results** | Maximum number of search results to display. | `5` |

## ⌨️ Usage

1.  **Open Ulauncher** and type `kp ` (or your configured keyword).
2.  **Unlock:** If the database is locked, a window will appear asking for your master password.
3.  **Search:** Type to find entries (e.g., `github`).
4.  **Action:** Select an entry to see the available options:

### Available Actions per Entry:
* **⌨️ Type Password / Username / URL:**
  * Uses Autotype to insert the text into the *last active window*.
  * *Tip:* Great for login forms where you don't want to copy-paste.
* **⏱️ Type TOTP:**
  * Types the current 2-Factor Authentication code.
* **📋 Copy [Attribute] (Secure):**
  * Copies the Password, Username, URL, or TOTP to the clipboard.
  * **Auto-Clears** after 10 seconds.

## 🛠 Troubleshooting

**The passphrase window doesn't appear / focus?**
* Ensure `wmctrl` is installed.
* Note: Wayland compositors might restrict window focus stealing.

**Clipboard is empty after "Success" notification?**
* Ensure `xclip` or `xsel` is installed. `keepassxc-cli` fails silently if no clipboard tool is available on Linux.

**Autotype types into the wrong window?**
* Autotype waits `0.5s` for Ulauncher to close. If your system is under heavy load, the focus might not switch back in time.

## 👨‍💻 Development

I use the following tools for this modernized version:
* **Formatting:** `black`
* **Linting:** `pylint`, `flake8`
* **Type Checking:** `mypy`

**Install dev dependencies:**
```bash
pip install -r scripts/requirements.txt
```
## 📜 License

MIT license. See [LICENSE](LICENSE) file for details.
