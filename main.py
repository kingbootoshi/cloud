import os
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional
from datetime import datetime, UTC
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mem0 import Memory
from neo4j import GraphDatabase

def setup_logger():
    """Configure logging with proper process safety for multiple workers"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(process)d - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    file_handler = RotatingFileHandler(
        filename=f'logs/api.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        delay=True
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(process)d - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
load_dotenv()

def init_neo4j_database():
    """
    Initialize Neo4j database with required schema and constraints.
    Only creates schema if it doesn't already exist.
    """
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        def check_schema_exists(tx):
            result = tx.run("""
                MATCH (schema:Schema {version: 'v1'})
                RETURN schema IS NOT NULL as exists
            """)
            return result.single()['exists']

        def init_schema(tx):
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Memory) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Memory) REQUIRE n.user_id IS NOT NULL",
                "CREATE INDEX IF NOT EXISTS FOR (n:Memory) ON (n.embedding)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Memory) ON (n.user_id)",
            ]
            for constraint in constraints:
                tx.run(constraint)

            tx.run("""
                CREATE (schema:Schema {
                    version: 'v1',
                    created_at: datetime(),
                    properties: ['embedding', 'user_id', 'agent_id', 'content', 'metadata']
                })
            """)

        with driver.session() as session:
            schema_exists = session.execute_read(check_schema_exists)
            if not schema_exists:
                logger.info("Initializing Neo4j schema for first time setup...")
                session.execute_write(init_schema)
                logger.info("Neo4j schema initialized successfully")
            else:
                logger.info("Neo4j schema already exists, skipping initialization")
        
        driver.close()
        return True
    except Exception as e:
        logger.error(f"Error initializing Neo4j database: {str(e)}")
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
- Create the facts based on the user and assistant messages only. Do not pick anything from the system messages.
- Make sure to return the response in the format mentioned in the examples. The response should be in json with a key as "facts" and corresponding value will be a list of strings.

!!! IMPORTANT !!!

IT IS VERY VERY IMPORTANT THAT YOU RETURN THE RESPONSE IN THE JSON FORMAT AS SHOWN ABOVE. PLEASE ONLY RETURN THIS JSON OUTPUT.

MANDATORY OUTPUT:
{{"facts": ["fact 1", "fact 2", "..."]}}
"""

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
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 1000
            }
        }
    },
    "custom_prompt": custom_prompt,
    "version": "v1.1"
}

if not init_neo4j_database():
    raise Exception("Failed to initialize Neo4j database. Please check your connection and credentials.")

memory_instance = Memory.from_config(config_dict=config)
app = FastAPI()

class MessageEntry(BaseModel):
    role: str
    content: str

class AddRequest(BaseModel):
    messages: List[MessageEntry]
    agent_id: str
    user_id: str
    metadata: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    query: str
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    limit: Optional[int] = 10

class GetAllRequest(BaseModel):
    agent_id: Optional[str] = None
    user_id: Optional[str] = None

@app.get("/ping")
def ping():
    """A simple ping endpoint to verify that the server is running."""
    return {"status": "ok", "message": "Memory server is up and running!"}

@app.post("/add")
def add_memory(req: AddRequest):
    try:
        request_details = {
            "endpoint": "/add",
            "agent_id": req.agent_id,
            "user_id": req.user_id,
            "metadata": req.metadata,
            "message_count": len(req.messages),
            "messages": [
                {
                    "role": msg.role,
                    "content_length": len(msg.content)
                } for msg in req.messages
            ]
        }
        logger.info(f"Incoming POST request to /add: {json.dumps(request_details, indent=2)}")
        
        # Convert MessageEntry objects to dictionaries
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in req.messages]
        
        start_time = datetime.now()
        response = memory_instance.add(
            messages_dict,  # Pass the converted dictionary list instead of MessageEntry objects
            agent_id=req.agent_id,
            user_id=req.user_id,
            metadata=req.metadata if req.metadata else {},
        )
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response_details = {
            "execution_time_seconds": execution_time,
            "status": "success",
            "response": response
        }
        logger.info(f"Response from /add: {json.dumps(response_details, indent=2)}")
        
        return {"status": "success", "result": response}
    except Exception as e:
        logger.error(f"Error adding memory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query_memory(req: QueryRequest):
    try:
        request_details = {
            "endpoint": "/query",
            "query": req.query,
            "agent_id": req.agent_id,
            "user_id": req.user_id,
            "limit": req.limit
        }
        logger.info(f"Incoming POST request to /query: {json.dumps(request_details, indent=2)}")
        
        kwargs = {}
        if req.agent_id:
            kwargs["agent_id"] = req.agent_id
        if req.user_id:
            kwargs["user_id"] = req.user_id
        if req.limit:
            kwargs["limit"] = req.limit

        start_time = datetime.now()
        result = memory_instance.search(req.query, **kwargs)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response_details = {
            "execution_time_seconds": execution_time,
            "results_count": len(result),
            "results": result
        }
        logger.info(f"Response from /query: {json.dumps(response_details, indent=2)}")
        
        return {"status": "success", "results": result}
    except Exception as e:
        logger.error(f"Error querying memory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_all")
def get_all_memories(req: GetAllRequest):
    try:
        request_details = {
            "endpoint": "/get_all",
            "agent_id": req.agent_id,
            "user_id": req.user_id
        }
        logger.info(f"Incoming POST request to /get_all: {json.dumps(request_details, indent=2)}")
        
        kwargs = {}
        if req.agent_id:
            kwargs["agent_id"] = req.agent_id
        if req.user_id:
            kwargs["user_id"] = req.user_id

        start_time = datetime.now()
        result = memory_instance.get_all(**kwargs)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response_details = {
            "execution_time_seconds": execution_time,
            "memories_count": len(result),
            "results": result
        }
        logger.info(f"Response from /get_all: {json.dumps(response_details, indent=2)}")
        
        return {"status": "success", "results": result}
    except Exception as e:
        logger.error(f"Error getting all memories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Memory API service - Process ID: {os.getpid()}")
    logger.info(f"Neo4j URI: {os.getenv('NEO4J_URI')}")
    logger.info(f"Qdrant URL: {os.getenv('QDRANT_URL')}")
    logger.info("Configuration loaded successfully")