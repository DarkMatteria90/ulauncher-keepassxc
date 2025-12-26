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
# ActionList und CopyToClipboardAction brauchen wir nicht mehr (Secure Copy regelt)

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
    Show details of an entry and trigger secure copy on enter.
    Updated to accept entry_name for the CLI call.
    """
    attrs = [
        ("Password", "password"),
        ("UserName", "username"),
        ("URL", "URL"),
        ("Notes", "notes"),
    ]
    items = []
    # ---Der Autotype Button (Ganz oben) ---
    items.append(
        ExtensionResultItem(
            icon="images/key.svg", # Oder ein anderes Icon, wenn du hast
            name="Perform Autotype",
            description="Type username and password into previous window",
            on_enter=ExtensionCustomAction({
                "action": "autotype",
                "entry": entry_name
            }, keep_app_open=False) # Wichtig: App muss zugehen!
        )
    )
    # --------------------------------------------
    for attr, attr_nice in attrs:
        val = details.get(attr, "")
        if val:
            # Wir rufen jetzt unsere Custom Action auf.
            # extension.py kümmert sich um den CLI-Aufruf und die Notification.
            action = ExtensionCustomAction({
                "action": "secure_copy",
                "entry": entry_name,
                "attr": attr # Wir übergeben den echten Attribut-Namen (z.B. "UserName")
            }, keep_app_open=False)

            if attr == "Password":
                items.append(
                    ExtensionSmallResultItem(
                        icon="images/copy.svg",
                        name="Copy password to the clipboard",
                        on_enter=action,
                    )
                )
            else:
                items.append(
                    ExtensionResultItem(
                        icon="images/copy.svg",
                        name="{}: {}".format(attr_nice.capitalize(), val),
                        description="Copy {} to the clipboard (Secure Copy)".format(attr_nice),
                        on_enter=action,
                    )
                )
    return RenderResultListAction(items)