import os
import json
from datetime import datetime


class MessageStore:
    """
    Class to handle storing and retrieving message history.
    """

    def __init__(self, storage_dir="storage"):
        """Initialize the message store with a storage directory."""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def get_user_file_path(self, user_name):
        """Get the file path for a specific user's chat history."""
        safe_username = user_name.lower().replace(" ", "_")
        return os.path.join(self.storage_dir, f"{safe_username}_chats.json")

    def save_chat(self, user_name, chat_id, chat_data):
        """Save a specific chat session to the user's storage."""
        file_path = self.get_user_file_path(user_name)

        # Load existing chats or create empty dict
        chats = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    chats = json.load(f)
            except json.JSONDecodeError:
                chats = {}

        # Update with new chat
        chats[chat_id] = chat_data

        # Save back to file
        with open(file_path, "w") as f:
            json.dump(chats, f, indent=2)

    def load_all_chats(self, user_name):
        """Load all chat sessions for a user."""
        file_path = self.get_user_file_path(user_name)

        if not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def load_chat(self, user_name, chat_id):
        """Load a specific chat session."""
        all_chats = self.load_all_chats(user_name)
        return all_chats.get(
            chat_id,
            {
                "messages": [],
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    # Keeping these for backward compatibility
    def save_messages(self, user_name, messages):
        """Legacy method - saves messages under a default chat ID."""
        chat_id = "default"
        chat_data = {
            "messages": messages,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.save_chat(user_name, chat_id, chat_data)

    def load_messages(self, user_name):
        """Legacy method - loads messages from default chat ID."""
        return self.load_chat(user_name, "default").get("messages", [])
