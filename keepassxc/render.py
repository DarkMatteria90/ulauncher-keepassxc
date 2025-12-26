"""
Functions that deal with rendering Ulauncher result items
"""
from typing import List, Dict
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

NO_SEARCH_RESULTS_ITEM = ExtensionResultItem(
    icon="images/not_found.svg",
    name="No matching entries found...",
    description="Please check spelling or make the query less specific",
    on_enter=DoNothingAction(),
)


def item_more_results_available(cnt: int) -> ResultItem:
    return ExtensionSmallResultItem(
        icon="images/empty.png",
        name="...{} more results available, please refine the search query...".format(
            cnt
        ),
        on_enter=DoNothingAction(),
    )


def cli_not_found_error() -> BaseAction:
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon="images/error.svg",
                name="Cannot execute keepassxc-cli",
                description="Please make sure keepassxc-cli is installed and accessible",
                on_enter=DoNothingAction(),
            )
        ]
    )


def db_file_not_found_error() -> BaseAction:
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon="images/error.svg",
                name="Cannot find the database file",
                description="Please verify database file path in extension preferences",
                on_enter=DoNothingAction(),
            )
        ]
    )


def keepassxc_cli_error(message: str) -> BaseAction:
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon="images/error.svg",
                name="Error while calling keepassxc CLI",
                description=message,
                on_enter=DoNothingAction(),
            )
        ]
    )


def ask_to_enter_passphrase(db_path: str) -> BaseAction:
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon="images/keepassxc-search-locked.svg",
                name="Unlock KeePassXC database",
                description=db_path,
                on_enter=ExtensionCustomAction({"action": "read_passphrase"}),
            )
        ]
    )


def ask_to_enter_query() -> BaseAction:
    return RenderResultListAction(
        [
            ExtensionResultItem(
                icon="images/keepassxc-search.svg",
                name="Enter search query...",
                description="Please enter your search query",
                on_enter=DoNothingAction(),
            )
        ]
    )


def search_results(
    keyword: str, arg: str, entries: List[str], max_items: int
) -> BaseAction:
    items = []
    if not entries:
        items.append(NO_SEARCH_RESULTS_ITEM)
    else:
        for entry in entries[:max_items]:
            action = ExtensionCustomAction(
                {
                    "action": "activate_entry",
                    "entry": entry,
                    "keyword": keyword,
                    "prev_query_arg": arg,
                },
                keep_app_open=True,
            )
            items.append(
                ExtensionSmallResultItem(
                    icon="images/key.svg", name=entry, on_enter=action
                )
            )
        if len(entries) > max_items:
            items.append(item_more_results_available(len(entries) - max_items))
    return RenderResultListAction(items)


def active_entry(entry_name: str, details: Dict[str, str]) -> BaseAction:
    """
    Show detailed actions including TOTP if available.
    """
    items = []

    # --- 1. Autotype / Type Helpers ---
    
    # Password (immer nützlich)
    if details.get("Password"):
        items.append(ExtensionSmallResultItem(
            icon="images/key.svg",
            name="Type Password",
            on_enter=ExtensionCustomAction({
                "action": "type_field",
                "entry": entry_name,
                "field": "Password"
            }, keep_app_open=False)
        ))

    # TOTP (Highlight! Zeigt den Code direkt an)
    if details.get("TOTP"):
        items.append(ExtensionSmallResultItem(
            icon="images/key.svg",
            name=f"Type TOTP: {details['TOTP']}",
            description="Types the current 2FA code",
            on_enter=ExtensionCustomAction({
                "action": "type_field",
                "entry": entry_name,
                "field": "TOTP"
            }, keep_app_open=False)
        ))

    # Username
    if details.get("UserName"):
        items.append(ExtensionSmallResultItem(
            icon="images/key.svg",
            name=f"Type Username: {details['UserName']}",
            on_enter=ExtensionCustomAction({
                "action": "type_field",
                "entry": entry_name,
                "field": "UserName"
            }, keep_app_open=False)
        ))

    # URL
    if details.get("URL"):
        items.append(ExtensionSmallResultItem(
            icon="images/key.svg",
            name=f"Type URL: {details['URL']}",
            on_enter=ExtensionCustomAction({
                "action": "type_field",
                "entry": entry_name,
                "field": "URL"
            }, keep_app_open=False)
        ))
        
    # --- 2. Copy Actions (Secure Copy) ---
    
    # TOTP Copy Button
    if details.get("TOTP"):
        items.append(ExtensionResultItem(
            icon="images/copy.svg",
            name="Copy TOTP to clipboard",
            description="Generates fresh code and clears clipboard after timeout",
            on_enter=ExtensionCustomAction({
                "action": "secure_copy",
                "entry": entry_name,
                "attr": "totp"
            }, keep_app_open=False)
        ))

    attrs = [
        ("Password", "password"),
        ("UserName", "username"),
        ("URL", "URL"),
        ("Notes", "notes"),
    ]
    
    for attr, attr_nice in attrs:
        val = details.get(attr, "")
        if val:
            action = ExtensionCustomAction({
                "action": "secure_copy",
                "entry": entry_name,
                "attr": attr
            }, keep_app_open=False)

            if attr == "Password":
                items.append(
                    ExtensionSmallResultItem(
                        icon="images/copy.svg",
                        name="Copy password to clipboard",
                        on_enter=action,
                    )
                )
            else:
                items.append(
                    ExtensionResultItem(
                        icon="images/copy.svg",
                        name="{}: {}".format(attr_nice.capitalize(), val),
                        description="Copy {} to clipboard (Secure)".format(attr_nice),
                        on_enter=action,
                    )
                )

    return RenderResultListAction(items)