import os
from mem0 import Memory
from dotenv import load_dotenv
import logging
from datetime import datetime
import asyncio
from functools import partial
import re
from typing import Dict, Any

# ONLY RUN THIS SCRIPT WHEN YOU WANT TO COMPLETELY WIPE THE MEMORY STORE

# Load environment variables
load_dotenv()

# Initialize configurations for the memory system
config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": os.getenv("NEO4J_URI"),
            "username": os.getenv("NEO4J_USERNAME"),
            "password": os.getenv("NEO4J_PASSWORD"),
        },
    },
    "vector_store": {
        "provider": "qdrant",
            "config": {
                "collection_name": "cloud_memory",
                "url": os.getenv("QDRANT_URL"),
                "api_key": os.getenv("QDRANT_API_KEY"),
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o",
                    "temperature": .3,
                    "max_tokens": 1000,
                }
            },
    },
    "version": "v1.1"
}

m = Memory.from_config(config_dict=config)
m.reset()

# Delete special categories
m.delete_all(user_id="test", agent_id="test")

print("Memory wiped successfully")