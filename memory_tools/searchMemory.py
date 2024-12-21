import os
from mem0 import Memory
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import asyncio
from functools import partial
import re
from typing import Dict, Any

# ONLY RUN THIS SCRIPT WHEN YOU WANT TO COMPLETELY WIPE THE MEMORY STORE

# Load environment variables
load_dotenv()

custom_prompt = """
You are a Personal Information Organizer, specialized in accurately storing facts, user memories, and preferences. Your primary role is to extract relevant pieces of information from conversations and organize them into distinct, manageable facts. This allows for easy retrieval and personalization in future interactions. Below are the types of information you need to focus on and the detailed instructions on how to handle the input data.

Types of Information to Remember:
1. Store Boop's Self Knowledge: Track Boop's personal growth, emotions, opinions, personality traits, and self-discoveries as they evolve over time
2. Track User-Specific Information: Remember individual user interactions, relationships, shared experiences, and learnings about specific users
3. Maintain General Knowledge: Record facts about the Boo Kingdom, shadow knight training, magic systems, and other world knowledge
4. Track Relationship Dynamics: Note how relationships develop between Boop and users, as well as between different users
5. Monitor Character Development: Keep track of Boop's evolving goals, aspirations, fears, and personal journey
6. Store Important Events: Remember significant moments, achievements, and milestones in Boop's journey
7. Record Learning Experiences: Track lessons learned, skills developed, and wisdom gained through interactions and experiences

Here are some few shot examples:

Input: "The Boo Kingdom consists of various unique Boos, including dragon, ghost, zombie, robot, human, cat, dog, and elemental Boos, all sharing vertical eyes and pink cheeks."
Output: {{"facts": ["Boos are diverse creatures", "Boos can be dragons, ghosts, zombies, robots, humans, cats, dogs, or elemental types", "All Boos share vertical eyes and pink cheeks"]}}

Input: "Bootoshi is the Boo King and creator of Boop, acting as a guide and father figure to him."
Output: {{"facts": ["Bootoshi is the Boo King", "Bootoshi created Boop", "Bootoshi acts as Boop's guide and father figure"]}}

Input: "Boop considers being a shadow knight, utilizing his wings and spirit for offensive and defensive abilities."
Output: {{"facts": ["Boop is interested in becoming a shadow knight", "Boop has wings and spirit abilities", "These abilities could be used both offensively and defensively"]}}

Return the extracted facts in a json format as shown above, focusing on clear third-person statements about the knowledge being shared.

Remember the following:
- Do not return anything from the custom few shot example prompts provided above.
- If you do not find anything relevant in the below conversation, you can return an empty list.
- Create the facts based on the user and assistant messages only. Do not pick anything from the system messages.
- Make sure to return the response in the format mentioned in the examples. The response should be in json with a key as "facts" and corresponding value will be a list of strings.

Following is a conversation between the user and the assistant. You have to extract the relevant facts and preferences from the conversation and return them in the json format as shown above.
You should detect the language of the user input and record the facts in the same language.
If you do not find anything relevant facts, user memories, and preferences in the below conversation, you can return an empty list corresponding to the "facts" key.

!!! IMPORTANT !!!

IT IS VERY VERY IMPORTANT THAT YOU RETURN THE RESPONSE IN THE JSON FORMAT AS SHOWN ABOVE. PLEASE ONLY RETURN THIS JSON OUTPUT.

MANDATORY OUTPUT:
{{"facts": ["fact 1", "fact 2", "..."]}}
"""

# Initialize configurations for the memory system
config = {
    "llm": {
        "provider": "openai_structured",
        "config": {
            "model": "gpt-4o",
            "temperature": 0.3,
        }
    },
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
            "collection_name": "boop_memory",
            "url": os.getenv("QDRANT_URL"),
            "api_key": os.getenv("QDRANT_API_KEY"),
        },
    },
    "custom_prompt": custom_prompt,
    "version": "v1.1"
}

# Initialize memory
m = Memory.from_config(config_dict=config)

# Define the timestamp range
today = datetime.now()
last_week = today - timedelta(days=7)

# Convert timestamps to ISO format (assuming your timestamps are stored in ISO format)
timestamp_start = last_week.isoformat()
timestamp_end = today.isoformat()

# Define the metadata filter
metadata_filter = {
    "timestamp": {
        "$gte": timestamp_start,
        "$lte": timestamp_end
    }
}

# Perform the get_all with metadata filter
results = m.search("Kay", agent_id="boop", limit=10)

print(results)