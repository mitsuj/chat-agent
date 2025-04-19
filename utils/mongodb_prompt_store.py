from pymongo import MongoClient
import json
from datetime import datetime
from config.mongodb_config import MONGODB_URI, DATABASE_NAME

# Collection name for prompts
PROMPTS_COLLECTION = "prompts"


class MongoDBPromptStore:
    """
    Class to handle storing and retrieving prompts using MongoDB.
    """

    def __init__(self):
        """Initialize the MongoDB prompt store."""
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.prompts_collection = self.db[PROMPTS_COLLECTION]

    def save_prompt(self, title, content):
        """Save a prompt to MongoDB."""
        # Create command from title (lowercase, replace spaces with dashes)
        command = "/" + title.lower().replace(" ", "-")

        # Create query filter to find existing document
        query = {"command": command}

        # Set update with prompt data
        update = {
            "$set": {
                "title": title,
                "command": command,
                "content": content,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        }

        # Upsert (update if exists, insert if not)
        self.prompts_collection.update_one(query, update, upsert=True)
        return command

    def get_all_prompts(self):
        """Get all prompts from MongoDB."""
        cursor = self.prompts_collection.find({})
        prompts = []
        for doc in cursor:
            # Remove MongoDB _id field for JSON serialization
            if "_id" in doc:
                del doc["_id"]
            prompts.append(doc)
        return prompts

    def delete_prompt(self, command):
        """Delete a prompt by its command."""
        self.prompts_collection.delete_one({"command": command})

    def get_prompt_by_command(self, command):
        """Get a prompt by its command."""
        prompt = self.prompts_collection.find_one({"command": command})
        if prompt and "_id" in prompt:
            del prompt["_id"]
        return prompt

    def export_prompts_to_json(self):
        """Export all prompts as JSON string."""
        prompts = self.get_all_prompts()
        return json.dumps(prompts, indent=2)

    def import_prompts_from_json(self, json_str):
        """Import prompts from JSON string."""
        try:
            prompts = json.loads(json_str)
            for prompt in prompts:
                if "title" in prompt and "content" in prompt:
                    self.save_prompt(prompt["title"], prompt["content"])
            return len(prompts)
        except json.JSONDecodeError:
            return 0
