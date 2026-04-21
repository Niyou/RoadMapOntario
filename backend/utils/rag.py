import os
from openai import AsyncOpenAI
from backend.db.mongo import get_client

# Initialize OpenAI Client
# This expects the OPENAI_API_KEY environment variable to be set.
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def retrieve_context(profession: str, top_k: int = 3) -> str:
    """
    Retrieves relevant regulatory context for a given profession from MongoDB 
    using Atlas Vector Search.
    """
    # 1. Generate an embedding for the search query
    query = f"Ontario licensing and education requirements for {profession}"
    
    response = await openai_client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_vector = response.data[0].embedding
    
    # 2. Connect to MongoDB and setup the target collection
    mongo_client = get_client()
    db = mongo_client["roadmap_ontario"]
    collection = db["regulatory_docs"]
    
    # 3. Define the $vectorSearch pipeline
    # Note: Ensure the "index" name matches the one created in Atlas UI.
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index", 
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": top_k * 10, # Typically 10x-20x the limit
                "limit": top_k
            }
        },
        {
            "$project": {
                "_id": 0,
                "source_url": 1,
                "text_chunk": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]
    
    # 4. Execute the aggregate pipeline
    cursor = collection.aggregate(pipeline)
    results = await cursor.to_list(length=top_k)
    
    # 5. Format the results
    if not results:
        return "No official context found."
        
    formatted_chunks = []
    for doc in results:
        source_url = doc.get("source_url", "Unknown Source")
        text_chunk = doc.get("text_chunk", "")
        formatted_chunks.append(f"--- Source: {source_url} ---\n{text_chunk}")
        
    return "\n\n".join(formatted_chunks)
