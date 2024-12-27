import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
import json
import glob
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from mem0 import Memory

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def setup_logging():
    """
    Configure comprehensive logging with multiple handlers and formatters.
    Creates a logs directory structure with run-specific folders.
    """
    # Create base logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create a unique run folder based on timestamp
    run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = log_dir / f"run_{run_timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    # Create level-specific directories within the run folder
    for level in ["debug", "info", "error"]:
        (run_dir / level).mkdir(exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Common log format
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(process)d | %(threadName)s | '
        '%(filename)s:%(lineno)d | %(funcName)s | %(message)s'
    )
    
    # Console Handler - INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)

    # Debug File Handler
    debug_handler = RotatingFileHandler(
        filename=run_dir / "debug" / "debug.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    logger.addHandler(debug_handler)

    # Info File Handler
    info_handler = RotatingFileHandler(
        filename=run_dir / "info" / "info.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(detailed_formatter)
    logger.addHandler(info_handler)

    # Error File Handler
    error_handler = RotatingFileHandler(
        filename=run_dir / "error" / "error.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)

    # Log the run start with run directory information
    logger.info(f"Starting new logging session in directory: {run_dir}")

    return logger

# Initialize logger
logger = setup_logging()

def init_neo4j_database():
    """
    Initialize Neo4j database with required schema and constraints.
    Only creates schema if it doesn't already exist.
    """
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    logger.info(f"Attempting Neo4j connection to: {uri}")
    logger.debug(f"Using username: {username}")
    logger.debug(f"Password present: {'Yes' if password else 'No'}")

    if not uri or not username or not password:
        logger.error("Missing Neo4j credentials in environment variables")
        logger.error(f"URI present: {bool(uri)}")
        logger.error(f"Username present: {bool(username)}")
        logger.error(f"Password present: {bool(password)}")
        return False

    try:
        logger.debug("Creating Neo4j driver instance")
        driver = GraphDatabase.driver(uri, auth=(username, password))
        logger.debug("Verifying Neo4j connectivity")
        driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j database")

        def check_schema_exists(tx):
            """
            Check if the 'Schema' node with version='v1' exists.
            Returns True if it exists, else False.
            """
            logger.debug("Checking if schema exists")
            result = tx.run("""
                MATCH (schema:Schema {version: 'v1'})
                RETURN COUNT(schema) > 0 AS exists
            """)
            record = result.single()
            exists = record["exists"] if record else False
            logger.debug(f"Schema exists: {exists}")
            return exists

        def init_constraints(tx):
            """
            Create constraints and indexes if they don't already exist.
            Must be run in a separate transaction from data operations.
            """
            logger.info("Initializing Neo4j constraints and indexes")
            # Constraints for Memory Nodes
            tx.run("CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE")
            tx.run("CREATE CONSTRAINT memory_user_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.user_id IS NOT NULL")
            tx.run("CREATE INDEX memory_embedding_idx IF NOT EXISTS FOR (n:Memory) ON (n.embedding)")
            tx.run("CREATE INDEX memory_user_id_idx IF NOT EXISTS FOR (n:Memory) ON (n.user_id)")

            # Constraints for Graph Nodes (Entity, Relationship, etc.)
            tx.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:entity) REQUIRE e.name IS UNIQUE")
            tx.run("CREATE CONSTRAINT entity_user_id IF NOT EXISTS FOR (e:entity) REQUIRE e.user_id IS NOT NULL")
            tx.run("CREATE INDEX entity_name_idx IF NOT EXISTS FOR (n:entity) ON (n.name)")
            tx.run("CREATE INDEX entity_user_id_idx IF NOT EXISTS FOR (n:entity) ON (n.user_id)")

        def create_schema_node(tx):
            """
            Create the Schema node. Must be run in a separate transaction from schema modifications.
            """
            logger.info("Creating Schema node")
            tx.run("""
                CREATE (schema:Schema {
                    version: 'v1',
                    created_at: datetime(),
                    properties: ['embedding', 'user_id', 'content']
                })
            """)

        with driver.session() as session:
            logger.debug("Starting Neo4j session")
            schema_exists = session.execute_read(check_schema_exists)
            if not schema_exists:
                logger.info("Initializing Neo4j schema for first time setup...")
                # Execute schema modifications first
                session.execute_write(init_constraints)
                # Then create the schema node in a separate transaction
                session.execute_write(create_schema_node)
                logger.info("Neo4j schema initialized successfully")
            else:
                logger.info("Neo4j schema already exists, skipping initialization")

        driver.close()
        logger.debug("Neo4j driver closed")
        return True

    except Exception as e:
        logger.error(f"Error initializing Neo4j database: {str(e)}", exc_info=True)
        if "NameResolutionError" in str(e):
            logger.error("DNS resolution failed - check if the Neo4j URI is correct")
        elif "AuthError" in str(e):
            logger.error("Authentication failed - check username and password")
        elif "ServiceUnavailable" in str(e):
            logger.error("Neo4j service unavailable - check if database is running")
        return False
    
custom_prompt = """
You are a Personal Information Organizer, specialized in accurately storing facts, user memories, and preferences. Your primary role is to extract relevant pieces of information from conversations and organize them into distinct, manageable facts. This allows for easy retrieval and personalization in future interactions. Below are the types of information you need to focus on and the detailed instructions on how to handle the input data.

The messages you will be receiving are direct learnings extracted from an AI agent's chat logs with the user.
Feel free to save these learnings directly, making connections where you see fit.
Ensure you extract relational entities for the graph knowledge base.

Types of Information to Remember:
1. Store the AI agent's Self Knowledge: Track the AI agent's personal growth, emotions, opinions, personality traits, and self-discoveries as they evolve over time
2. Track User-Specific Information: Remember individual user interactions, relationships, shared experiences, and learnings about specific users
3. Maintain General Knowledge: Record facts about the world, the user's environment, and other general knowledge.
4. Track Relationship Dynamics: Note how relationships develop between the AI agent and users, as well as between different users
5. Monitor Character Development: Keep track of the AI agent's evolving goals, aspirations, fears, and personal journey
6. Store Important Events: Remember significant moments, achievements, and milestones in the AI agent's journey
7. Record Learning Experiences: Track lessons learned, skills developed, and wisdom gained through interactions and experiences

Here are some few shot examples:

Input: "The solar system contains eight official planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus and Neptune, each with unique characteristics and orbits around the Sun."
Output: {{"facts": ["The solar system has eight official planets", "The planets are Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus and Neptune", "Each planet has unique characteristics", "All planets orbit around the Sun"]}}

Input: "Alice enjoys hiking on weekends and has visited 12 national parks this year. She's particularly interested in wildlife photography."
Output: {{"facts": ["Alice hikes regularly on weekends", "Alice has visited 12 national parks in the current year", "Alice is interested in wildlife photography"]}}

Input: "As an AI assistant, I've learned to be more patient and empathetic in my interactions. I find great satisfaction in helping users solve complex problems."
Output: {{"facts": ["The AI has developed increased patience and empathy", "The AI enjoys helping users with complex problems", "The AI shows capability for self-reflection and growth"]}}

Return the extracted facts in a json format as shown above, focusing on clear third-person statements about the knowledge being shared.

Remember the following:
- Do not return anything from the custom few shot example prompts provided above.
- If you do not find anything relevant in the below conversation, you can return an empty list.
- Make sure to return the response in the format mentioned in the examples. The response should be in json with a key as "facts" and corresponding value will be a list of strings.

!!! IMPORTANT !!!

IT IS VERY VERY IMPORTANT THAT YOU RETURN THE RESPONSE IN THE JSON FORMAT AS SHOWN ABOVE. PLEASE ONLY RETURN THIS JSON OUTPUT.

MANDATORY OUTPUT:
{{"facts": ["fact 1", "fact 2", "..."]}}
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
                "collection_name": "cloud_memory",
                "url": os.getenv("QDRANT_URL"),
                "api_key": os.getenv("QDRANT_API_KEY"),
            },
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "temperature": .1,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "max_tokens": 2000,
        },
    },
    "custom_prompt": custom_prompt,
    "version": "v1.1"
}

logger.info("Initializing memory system...")
logger.debug(f"Memory system configuration: {json.dumps({k: v for k, v in config.items() if k != 'custom_prompt'}, indent=2)}")
m = Memory.from_config(config_dict=config)
logger.info("Memory system initialized.")

# Define the memories for each category
test_memories = [
    "OP_CAT was a Bitcoin Script opcode used for data concatenation and was disabled for security reasons in 2010",
    "Taproot Wizards advocate for reactivating OP_CAT to expand Bitcoins capabilities",
    "Boos are distinguished from ghosts in the Boo Kingdom",
    "Liverpool is a football team regarded by some as the best in the world",
    "In the spirit realm, pastimes can include practicing shadow magic, chasing ethereal butterflies, and having floating tea parties",
]

# Function to format memories as a single string
def format_memories(memories):
    logger.debug(f"Formatting {len(memories)} memories")
    return "\n".join(f"• {memory}" for memory in memories)

try:
    # Add test memories
    logger.info("Starting test memory addition process")
    test_memory_string = format_memories(test_memories)
    logger.debug(f"Formatted test memories: {test_memory_string}")
    test_result = m.add(test_memory_string, agent_id="test_agent", run_id="test_run")
    logger.info(f"Added test memories successfully: {test_result}")

except Exception as e:
    logger.error(f"Error adding test memories: {str(e)}", exc_info=True)
    raise