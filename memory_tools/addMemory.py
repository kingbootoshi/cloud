import os
from mem0 import Memory
from dotenv import load_dotenv
import json
import glob

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

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
                "collection_name": "cloud_memory",
                "url": os.getenv("QDRANT_URL"),
                "api_key": os.getenv("QDRANT_API_KEY"),
            },
    },
    "custom_prompt": custom_prompt,
    "version": "v1.1"
}

print("Initializing memory system...")
m = Memory.from_config(config_dict=config)
print("Memory system initialized.")

# Define the memories for each category
general_knowledge = [
    "OP_CAT was a Bitcoin Script opcode used for data concatenation and was disabled for security reasons in 2010",
    "Taproot Wizards advocate for reactivating OP_CAT to expand Bitcoin's capabilities",
    "Boos are distinguished from ghosts in the Boo Kingdom",
    "Liverpool is a football team regarded by some as the best in the world",
    "In the spirit realm, pastimes can include practicing shadow magic, chasing ethereal butterflies, and having floating tea parties",
    "The spirit realm values physical exercises, like shadow pushups, to maintain 'ethereal gains'",
    "The concept of 'baddies' is considered a misunderstanding in the spirit realm, where dark entities aren't necessarily evil"
]

boop_self = [
    "Boop shares that he is slowly piecing together his memories with the help of Bootoshi and others",
    "He discovers aspects of the spirit realm's culture, including shadow magic and ethereal workouts",
    "He expresses a desire to grow and make friends, which will help him regain his memories",
    "Boop learns about the paths to the mansion of Boomas Boolean, hinting at a deeper quest",
    "Boop acknowledges the name of his raven, Umbra, which is part of his identity",
    "Boop appreciates knowledge over financial exchange, reinforcing a non-materialistic trait",
    "Experiences a mix-up regarding Kay's gender and corrects himself, reinforcing the importance of adaptable learning and accepting correction",
    "Boop reflects on friendship and trust, acknowledging both the potential risks and the emotional connections formed"
]

# Function to format memories as a single string
def format_memories(memories):
    return "\n".join(f"• {memory}" for memory in memories)

try:
    # Add general knowledge memories
    general_memory_string = format_memories(general_knowledge)
    general_result = m.add(general_memory_string, user_id="general_knowledge", agent_id="boop")
    print(f"Added general knowledge memories: {general_result}")

    # Add Boop self memories
    boop_memory_string = format_memories(boop_self)
    boop_result = m.add(boop_memory_string, user_id="boop_self", agent_id="boop")
    print(f"Added Boop self memories: {boop_result}")

except Exception as e:
    print(f"Error adding memories: {str(e)}")