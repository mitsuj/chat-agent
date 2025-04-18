import os
from datetime import datetime
from pymongo import MongoClient
from config.mongodb_config import MONGODB_URI, DATABASE_NAME, CHATS_COLLECTION


class MongoDBMessageStore:
    """
    Class to handle storing and retrieving message history using MongoDB.
    """

    def __init__(self):
        """Initialize the MongoDB message store."""
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.chats_collection = self.db[CHATS_COLLECTION]

    def get_safe_username(self, user_name):
        """Convert username to a safe format."""
        return user_name.lower().replace(" ", "_")

    def save_chat(self, user_name, chat_id, chat_data):
        """Save a specific chat session to MongoDB."""
        safe_username = self.get_safe_username(user_name)

        # Create query filter to find existing document
        query = {"user_name": safe_username, "chat_id": chat_id}

        # Set update with new chat data
        update = {
            "$set": {
                "user_name": safe_username,
                "chat_id": chat_id,
                "messages": chat_data["messages"],
                "last_updated": chat_data["last_updated"],
            }
        }

        # Upsert (update if exists, insert if not)
        self.chats_collection.update_one(query, update, upsert=True)

    def load_all_chats(self, user_name):
        """Load all chat sessions for a user from MongoDB."""
        safe_username = self.get_safe_username(user_name)

        # Find all chats for this user
        cursor = self.chats_collection.find({"user_name": safe_username})

        # Convert to dictionary format matching the original implementation
        chats = {}
        for doc in cursor:
            chat_id = doc["chat_id"]
            chats[chat_id] = {
                "messages": doc["messages"],
                "last_updated": doc["last_updated"],
            }

        return chats

    def load_chat(self, user_name, chat_id):
        """Load a specific chat session from MongoDB."""
        safe_username = self.get_safe_username(user_name)

        # Find the specific chat
        doc = self.chats_collection.find_one(
            {"user_name": safe_username, "chat_id": chat_id}
        )

        if doc:
            return {"messages": doc["messages"], "last_updated": doc["last_updated"]}
        else:
            return {
                "messages": [],
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

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
