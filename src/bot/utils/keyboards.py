"""Keyboard utilities for persistent reply keyboards and command palette."""

from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# Button labels (these are the text users tap)
BTN_PROJECTS = "📁 Projects"
BTN_NEW_SESSION = "🆕 New Session"
BTN_STATUS = "📊 Status"
BTN_MENU = "📋 Menu"
BTN_ACTIONS = "⚡ Actions"
BTN_GIT = "🔀 Git"
BTN_EXPORT = "📤 Export"
BTN_END = "🔚 End Session"

# Map button labels to their slash command equivalents
BUTTON_COMMAND_MAP: dict[str, str] = {
    BTN_PROJECTS: "/projects",
    BTN_NEW_SESSION: "/new",
    BTN_STATUS: "/status",
    BTN_MENU: "/menu",
    BTN_ACTIONS: "/actions",
    BTN_GIT: "/git",
    BTN_EXPORT: "/export",
    BTN_END: "/end",
}


def get_main_keyboard(session_active: bool) -> ReplyKeyboardMarkup:
    """Return the persistent bottom keyboard based on session state.

    No session:     [Projects, New Session] [Status, Menu]
    Active session: [Actions, Git] [Status, Export] [End Session, Menu]
    """
    if session_active:
        buttons = [
            [BTN_ACTIONS, BTN_GIT],
            [BTN_STATUS, BTN_EXPORT],
            [BTN_END, BTN_MENU],
        ]
    else:
        buttons = [
            [BTN_PROJECTS, BTN_NEW_SESSION],
            [BTN_STATUS, BTN_MENU],
        ]

    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_menu_keyboard() -> InlineKeyboardMarkup:
    """Return the full command palette organized by category."""
    keyboard = [
        # Navigation
        [InlineKeyboardButton("━━ 📂 Navigation ━━", callback_data="menu:noop")],
        [
            InlineKeyboardButton("📁 Projects", callback_data="action:show_projects"),
            InlineKeyboardButton("📂 List Files", callback_data="action:ls"),
            InlineKeyboardButton("📍 Current Dir", callback_data="action:pwd"),
        ],
        # Session
        [InlineKeyboardButton("━━ 💻 Session ━━", callback_data="menu:noop")],
        [
            InlineKeyboardButton("🆕 New Session", callback_data="action:new_session"),
            InlineKeyboardButton("▶️ Continue", callback_data="action:continue"),
        ],
        [
            InlineKeyboardButton("🔚 End Session", callback_data="action:end_session"),
            InlineKeyboardButton("📊 Status", callback_data="action:status"),
        ],
        # Tools
        [InlineKeyboardButton("━━ 🔧 Tools ━━", callback_data="menu:noop")],
        [
            InlineKeyboardButton("⚡ Quick Actions", callback_data="action:quick_actions"),
            InlineKeyboardButton("🔀 Git", callback_data="action:git"),
        ],
        [
            InlineKeyboardButton("📤 Export", callback_data="action:export"),
        ],
        # Info
        [InlineKeyboardButton("━━ ℹ️ Info ━━", callback_data="menu:noop")],
        [
            InlineKeyboardButton("❓ Help", callback_data="action:help"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def is_keyboard_button(text: str) -> bool:
    """Check if the given text matches a known keyboard button label."""
    return text in BUTTON_COMMAND_MAP


def get_command_for_button(text: str) -> Optional[str]:
    """Return the slash command equivalent for a button label, or None."""
    return BUTTON_COMMAND_MAP.get(text)
