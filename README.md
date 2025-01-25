# Cloud - An Advanced AI Memory Server

![S7_bLThYdqvBzEbyyXJUb_3f419c2882044d539687769758c7b919](https://github.com/user-attachments/assets/b047961a-ba1f-41bd-90dc-c407549a1fb9)

Cloud acts as the central memory hub for all my AI agents. This is a customized mem0 server that uses Neo4j for graph_store and Qdrant for vector_store.

## TO-DO
- Create mailbox system for shared communication through all my AI apps

The mem0 package included in this repo is a modified version of the mem0 package from the [mem0ai](https://github.com/mem0ai/mem0) repo.

- `/add` allows you to add memories by passing a memory string, plus `agent_id`, `run_id`, `user_id`, and optional parameters:
  - `metadata`: Additional information about the memory (timestamps, etc.)
  - `skip_extraction`: (bool, default=False) If True, bypasses LLM fact-extraction and stores raw content directly
  - `store_mode`: (str, default="both") Where to store memories - options are "both", "vector", or "graph"
    - Note: When `skip_extraction=True`, `store_mode` must be "vector" as graph storage requires fact extraction
    (Skip extraction was created to store raw, un-edited memories in the vector store to keep FULL details, typically used for business or story knowledge for RAG.)

- `/query` allows you to search the stored memories with a query string, plus optional `agent_id`, `run_id`, `user_id`, and `limit`.
- `/get_all` allows you to retrieve all memories filtered by `agent_id`, `run_id`, and/or `user_id`.

How we treat mem0 functions:
- "agent_id" is the name of the agent that is making the memory.
- "run_id" is the category of memories. In my specific use case, my 3 main categories are "general_knowledge", "agent_specific", and "user_specific".
- "user_id" is the id of the user that is making the memory. optional, only invoked when called user_specific memories
- "metadata" is any additional information you want to store about the memory. timestamps, etc.

**Installation & Running:**  
1. Install dependencies:
   ```bash
   pip install fastapi uvicorn mem0 python-dotenv neo4j qdrant-client openai requests
   ```
   Make sure you have environment variables set for your Neo4j and Qdrant instances (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `QDRANT_URL`, `QDRANT_API_KEY`, and `OPENAI_API_KEY` if needed). You can store them in a `.env` file, also including `CLOUD_PASSWORD` for your API password.
   
2. Save the code in a file called `main.py`.
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
4. The API is available at `http://127.0.0.1:8000`.

**Authentication**  
- Every endpoint except `/ping` requires a header named **`X-Password`**.  
- The value must match `CLOUD_PASSWORD` from your `.env` file.

`**Example Usage:**

1. Adding Memories (`/add`):
```bash
curl -X POST "http://127.0.0.1:8000/add" \
-H "Content-Type: application/json" \
-H "X-Password: supersecret" \
-d '{
    "memories": "The user enjoys programming in Python and has been coding for 5 years",
    "agent_id": "assistant_1",
    "run_id": "user_specific",
    "user_id": "user123",
    "metadata": {
        "timestamp": "2024-03-20T10:30:00Z",
        "confidence": 0.95
    },
    "skip_extraction": false,
    "store_mode": "both"
}'
```

2. Querying Memories (`/query`):
```bash
curl -X POST "http://127.0.0.1:8000/query" \
-H "Content-Type: application/json" \
-H "X-Password: supersecret" \
-d '{
    "query": "What does the user like to program in?",
    "agent_id": "assistant_1",
    "run_id": "user_specific",
    "user_id": "user123",
    "limit": 5
}'
```

3. Getting All Memories (`/get_all`):
```bash
curl -X POST "http://127.0.0.1:8000/get_all" \
-H "Content-Type: application/json" \
-H "X-Password: supersecret" \
-d '{
    "agent_id": "assistant_1",
    "run_id": "user_specific",
    "user_id": "user123"
}'
```

Example Response Formats:

1. `/add` Response:
```json
{
    "status": "success",
    "result": {
        "results": [
            {
                "id": "1687c7c3-39ee-47fd-ad54-2f75a896c5df",
                "memory": "Quest Boo feels flustered when talking about his crush",
                "event": "ADD"
            }
        ],
        "relations": {
            "deleted_entities": [
                [
                    {
                        "source": "quest_boo",
                        "destination": "quest_boo",
                        "deleted_relationship": "has_playful_nature"
                    }
                ]
            ],
            "added_entities": [
                [
                    {
                        "source": "quest_boo",
                        "relationship": "feels_flustered_when_talking_about",
                        "destination": "crushes"
                    }
                ]
            ]
        }
    }
}
```

2. `/query` Response:
```json
{
    "status": "success",
    "results": {
        "results": [
            {
                "id": "efd686f0-ff03-4a55-bcc3-5b5b40a00c67",
                "memory": "Bootoshi is curious about Quest Boo's crush",
                "hash": "7b18682503050e415ea070b73a445e6d",
                "metadata": {
                    "timestamp": "2024-12-27T22:47:07.299Z"
                },
                "score": 0.18003586,
                "created_at": "2024-12-27T14:47:11.745369-08:00",
                "updated_at": null,
                "user_id": "1071515159748681888",
                "agent_id": "quest_boo",
                "run_id": "user_specific_knowledge"
            }
        ],
        "relations": []
    }
}
```

3. `/get_all` Response:
```json
{
    "status": "success",
    "results": {
        "results": [
            {
                "id": "efd686f0-ff03-4a55-bcc3-5b5b40a00c67",
                "memory": "Bootoshi is curious about Quest Boo's crush",
                "hash": "7b18682503050e415ea070b73a445e6d",
                "metadata": {
                    "timestamp": "2024-12-27T22:47:07.299Z"
                },
                "created_at": "2024-12-27T14:47:11.745369-08:00",
                "updated_at": null,
                "user_id": "1071515159748681888",
                "agent_id": "quest_boo",
                "run_id": "user_specific_knowledge"
            }
        ],
        "relations": []
    }
}
```

This approach allows any external service (like a TypeScript-based agent) to hit this Python API and leverage the `mem0` memory backend.
