import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from mem0.memory.main import Memory  # Import Memory class from local mem0 folder

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
    },
    "version": "v1.1"
}

# Initialize memory
m = Memory.from_config(config_dict=config)

search_query = "<@1074617018218717204> tell me about discord"

# Perform the get_all with metadata filter
results = m.search(search_query, agent_id="quest_boo", run_id="general_knowledge")

print(f"Search results for query {search_query}: {results}")