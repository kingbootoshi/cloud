import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime
import asyncio
from functools import partial
import re
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from mem0 import Memory

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
                "collection_name": "test",
                "url": os.getenv("QDRANT_URL"),
                "api_key": os.getenv("QDRANT_API_KEY"),
            },
    },
    "version": "v1.1"
}

m = Memory.from_config(config_dict=config)
m.reset() # Wipes vector DB

# Delete_all must be used to wipe the knowledge graph DB

# Delete only the agent
m.delete_all(agent_id="test_agent")

print("Memory wiped successfully")