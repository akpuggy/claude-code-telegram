"""Quick Actions feature implementation.

Provides context-aware quick action suggestions for common development tasks.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.storage.models import SessionModel

logger = logging.getLogger(__name__)


@dataclass
class QuickAction:
    """Represents a quick action suggestion."""

    id: str
    name: str
    description: str
    command: str
    icon: str
    category: str
    context_required: List[str]  # Required context keys
    priority: int = 0  # Higher = more important


class QuickActionManager:
    """Manages quick action suggestions based on context."""

    def __init__(self) -> None:
        """Initialize the quick action manager."""
        self.actions = self._create_default_actions()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _create_default_actions(self) -> Dict[str, QuickAction]:
        """Create PAI Second Brain quick actions."""
        # Note: Commands must be simple - the Telegram bot blocks curl, pipes, semicolons, etc.
        # Use direct tool calls (Read, Glob) not shell commands
        return {
            "pending_tasks": QuickAction(
                id="pending_tasks",
                name="Pending Tasks",
                description="Show pending tasks from PAI memory",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Use the Glob tool to find files in /home/pai/.claude/MEMORY/WORK/ then Read the most recent META.yaml files to show my pending tasks. Be concise.",
                icon="📋",
                category="tasks",
                context_required=[],
                priority=10,
            ),
            "quick_note": QuickAction(
                id="quick_note",
                name="Quick Note",
                description="Capture a quick note to inbox",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Ask me what I want to remember, then save it as a timestamped markdown file in /home/pai/.claude/MEMORY/INBOX/ using the Write tool.",
                icon="💡",
                category="capture",
                context_required=[],
                priority=9,
            ),
            "reminders": QuickAction(
                id="reminders",
                name="Reminders",
                description="Check upcoming reminders",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Use Glob and Read tools to check /home/pai/.claude/MEMORY/ for any reminder or scheduled items. List them briefly.",
                icon="🔔",
                category="schedule",
                context_required=[],
                priority=8,
            ),
            "recent_learnings": QuickAction(
                id="recent_learnings",
                name="Recent Learnings",
                description="Review recent learnings captured by PAI",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Use Glob to find recent files in /home/pai/.claude/MEMORY/LEARNING/ and Read the 3 most recent ones. Summarize briefly.",
                icon="📚",
                category="review",
                context_required=[],
                priority=7,
            ),
            "search_memory": QuickAction(
                id="search_memory",
                name="Search Memory",
                description="Search PAI knowledge base",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Ask me what to search for, then use Grep to search /home/pai/.claude/MEMORY/ for matching content.",
                icon="🔍",
                category="recall",
                context_required=[],
                priority=6,
            ),
            "work_summary": QuickAction(
                id="work_summary",
                name="Work Summary",
                description="Summarize current active work",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Use Glob to find the most recent directory in /home/pai/.claude/MEMORY/WORK/ and Read its META.yaml and THREAD.md to summarize current work.",
                icon="📊",
                category="context",
                context_required=[],
                priority=5,
            ),
            "active_goals": QuickAction(
                id="active_goals",
                name="Active Goals",
                description="Show active goals from TELOS",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Use Read tool to read /home/pai/.claude/skills/PAI/USER/TELOS/PROJECTS.md and summarize my active goals briefly.",
                icon="🎯",
                category="goals",
                context_required=[],
                priority=4,
            ),
            "continue_last": QuickAction(
                id="continue_last",
                name="Continue Last",
                description="Resume last Claude session",
                command="IMPORTANT: Do NOT use the PAI Algorithm format. Just directly answer. Use Glob to find the most recent session in /home/pai/.claude/MEMORY/WORK/, Read its context, and ask how I want to continue.",
                icon="💬",
                category="flow",
                context_required=[],
                priority=3,
            ),
        }

    async def get_suggestions(
        self,
        session: Optional[SessionModel] = None,
        limit: int = 8,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> List[QuickAction]:
        """Get quick action suggestions.

        PAI Second Brain actions are always available (no context filtering).

        Args:
            session: Current session (optional, for backwards compatibility)
            limit: Maximum number of suggestions
            session_data: Dict with working_directory and user_id (alternative interface)

        Returns:
            List of suggested actions
        """
        try:
            # PAI actions have no context requirements - return all sorted by priority
            available_actions = list(self.actions.values())
            available_actions.sort(key=lambda x: x.priority, reverse=True)
            return available_actions[:limit]

        except Exception as e:
            self.logger.error(f"Error getting suggestions: {e}")
            return []

    def create_inline_keyboard(
        self, actions: List[QuickAction], columns: int = 2, max_columns: int = None
    ) -> InlineKeyboardMarkup:
        """Create inline keyboard for quick actions.

        Args:
            actions: List of actions to display
            columns: Number of columns in keyboard
            max_columns: Alias for columns (for backwards compatibility)

        Returns:
            Inline keyboard markup
        """
        # Support both parameter names
        cols = max_columns if max_columns is not None else columns
        keyboard = []
        row = []

        for i, action in enumerate(actions):
            button = InlineKeyboardButton(
                text=f"{action.icon} {action.name}",
                callback_data=f"quick_action:{action.id}",
            )
            row.append(button)

            # Add row when full or last item
            if len(row) >= cols or i == len(actions) - 1:
                keyboard.append(row)
                row = []

        return InlineKeyboardMarkup(keyboard)

    async def execute_action(
        self, action_id: str, session: SessionModel, callback: Optional[Callable] = None
    ) -> str:
        """Execute a quick action.

        Args:
            action_id: ID of action to execute
            session: Current session
            callback: Optional callback for command execution

        Returns:
            Command to execute
        """
        action = self.actions.get(action_id)
        if not action:
            raise ValueError(f"Unknown action: {action_id}")

        self.logger.info(
            f"Executing quick action: {action.name} for session {session.id}"
        )

        # Return the command - actual execution is handled by the bot
        return action.command
