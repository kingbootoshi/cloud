This is a fully self-contained example script of a FastAPI server that uses `mem0` to store and retrieve memories. It references the kind of configuration you used in your original code (Neo4j for graph_store and Qdrant for vector_store) and provides three endpoints: `/add`, `/query`, and `/get_all`. 

The mem0 package included in this repo is a modified version of the mem0 package from the [mem0ai](https://github.com/mem0ai/mem0) repo.

**What this code does:**  
- It sets up a FastAPI application and initializes a `Memory` instance from `mem0` using a configuration similar to what you described.
- `/add` allows you to add memories by passing an array of messages (each with `role` and `content`) plus `agent_id`, `user_id`, and optional `metadata`.
- `/query` allows you to search the stored memories with a query string, plus optional `agent_id`, `user_id`, and `limit`.
- `/get_all` allows you to retrieve all memories filtered by `agent_id` and/or `user_id`.

**Installation & Running:**  
1. Install dependencies:
   ```bash
   pip install fastapi uvicorn mem0 python-dotenv neo4j qdrant-client openai requests
   ```
   Make sure you have environment variables set for your Neo4j and Qdrant instances (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `QDRANT_URL`, `QDRANT_API_KEY`, and `OPENAI_API_KEY` if needed). You can store them in a `.env` file.
   
2. Save the code in a file called `memory_api.py`.
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
   
4. The API is available at `http://127.0.0.1:8000`.

**How to Use:**  
- **Add Memories:**  
  ```bash
  curl -X POST http://127.0.0.1:8000/add \
    -H "Content-Type: application/json" \
    -d '{
          "messages": [
            {"role": "user", "content": "I'\''m planning a trip to Japan next month."},
            {"role": "assistant", "content": "That'\''s exciting! Would you like recommendations?"}
          ],
          "agent_id": "agent_name",
          "user_id": "user_specific",
          "metadata": {"timestamp": "2024-12-18T12:00:00Z", "username": "alex"}
        }'
  ```

- **Query Memories:**  
  ```bash
  curl -X POST http://127.0.0.1:8000/query \
    -H "Content-Type: application/json" \
    -d '{
          "query": "japan",
          "agent_id": "agent_name",
          "user_id": "user_specific",
          "limit": 5
        }'
  ```

- **Get All Memories:**  
  ```bash
  curl -X POST http://127.0.0.1:8000/get_all \
    -H "Content-Type: application/json" \
    -d '{
          "agent_id": "agent_name",
          "user_id": "user_specific"
        }'
  ```

This approach allows any external service (like a TypeScript-based agent) to hit this Python API and leverage the `mem0` memory backend.