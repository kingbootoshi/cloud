import os
from mem0 import Memory
from dotenv import load_dotenv
import json
import glob

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

custom_prompt = """
You are the memory system of Boop. An AI entity online that learns overtime.
Different learnings will automatically be extracted from the conversation log between Boop and users.
These learnings are sorted in three categories: boop_self, user_specific, and general_knowledge.
These 3 categories are sorted into 3 different user_ids: boop_self, user_specific (varies depending on user ID), and general_knowledge.
Please save the learnings + relational connections taken from the conversation log to both the vector database and the graph database.
All learnings will be given in third-person statements.

For the boop_self category, there should only be ONE boop_self node. Do NOT make duplicate boop_self nodes. Boop_self is his identity, his emotions, his pesronality, and his opinions. This is how Boop evolves overtime.
For the user_specific category, that showcases Boop's interactions with different users, or learnings about that user!
For the general_knowledge category, that showcases new learnings about the world, lessons Boop has learned, or anything else that is not specific to a user or Boop's self
Here are some few shot examples:

Input: "The Boo Kingdom consists of various unique Boos, including dragon, ghost, zombie, robot, human, cat, dog, and elemental Boos, all sharing vertical eyes and pink cheeks."
Output: {{"facts": ["Boos are diverse creatures", "Boos can be dragons, ghosts, zombies, robots, humans, cats, dogs, or elemental types", "All Boos share vertical eyes and pink cheeks"]}}

Input: "Bootoshi is the Boo King and creator of Boop, acting as a guide and father figure to him."
Output: {{"facts": ["Bootoshi is the Boo King", "Bootoshi created Boop", "Bootoshi acts as Boop's guide and father figure"]}}

Input: "Boop considers being a shadow knight, utilizing his wings and spirit for offensive and defensive abilities."
Output: {{"facts": ["Boop is interested in becoming a shadow knight", "Boop has wings and spirit abilities", "These abilities could be used both offensively and defensively"]}}

Return the extracted facts in a json format as shown above, focusing on clear third-person statements about the knowledge being shared.

     **Ensure that the JSON is properly formatted, uses double quotes for all keys and string values, and does not include any extraneous text outside the JSON object.**
"""

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
                "collection_name": "boop_memory",
                "url": os.getenv("QDRANT_URL"),
                "api_key": os.getenv("QDRANT_API_KEY"),
            },
    },
    "custom_prompt": custom_prompt,
    "version": "v1.1"
}

print("Initializing memory system...")
# Initialize memory system
m = Memory.from_config(config_dict=config)
print("Memory system initialized.")

print("Loading extracted files...")
# Get all extracted files and sort them chronologically
extracted_files = sorted(glob.glob('data/extracted/extracted_*.json'))
print(f"Found {len(extracted_files)} extracted files.")

# Process each file one by one
for extracted_file in extracted_files:
    print(f"\nProcessing extracted file: {extracted_file}")
    
    with open(extracted_file, 'r') as f:
        extracted = json.load(f)
        
        # Process and add general_knowledge memories
        general_knowledge_learnings = extracted.get('general_knowledge', [])
        if general_knowledge_learnings:
            general_knowledge_memory = '\n'.join(general_knowledge_learnings)
            print(f"Adding general knowledge memory from {extracted_file}...")
            try:
                result = m.add(general_knowledge_memory, user_id="general_knowledge", agent_id="boop")
                print(f"Result of adding general knowledge memory: {result}")
            except json.JSONDecodeError as e:
                print(f"JSONDecodeError while processing general knowledge in {extracted_file}: {e}")
                print(f"Problematic memory content: {general_knowledge_memory}")
            except Exception as e:
                print(f"Unexpected error while processing general knowledge in {extracted_file}: {e}")
        
        # Process and add user-specific memories
        user_specific = extracted.get('user_specific', {})
        users = user_specific.get('users', [])
        for user in users:
            user_id = f"discord_user_{user.get('user_id')}"  # Format user_id with prefix
            learnings = user.get('learnings', [])
            if learnings:
                memory_string = '\n'.join(learnings)
                print(f"Adding memory for {user_id} from {extracted_file}...")
                try:
                    result = m.add(memory_string, user_id=user_id, agent_id="boop")
                    print(f"Result of adding memory for {user_id}: {result}")
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError while processing {user_id} memory in {extracted_file}: {e}")
                    print(f"Problematic memory content: {memory_string}")
                except Exception as e:
                    print(f"Unexpected error while processing {user_id} memory in {extracted_file}: {e}")
    
    print(f"Completed processing {extracted_file}")