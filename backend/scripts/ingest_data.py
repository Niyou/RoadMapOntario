"""
Script to ingest mock regulatory data into MongoDB and generate embeddings using OpenAI.

To use vector search in MongoDB Atlas, you must manually create a Vector Search Index
on the `regulatory_docs` collection. 

Instructions for creating the $vectorSearch index:
1. Go to your cluster in the MongoDB Atlas UI.
2. Click "Atlas Search" -> "Create Search Index".
3. Select "Atlas Vector Search" (JSON Editor).
4. Select the database `roadmap_ontario` and collection `regulatory_docs`.
5. Enter the following JSON configuration:
{
  "fields": [
    {
      "numDimensions": 1536,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
6. Name the index (e.g., "vector_index") and click "Create Search Index".
Note: text-embedding-3-small generates 1536 dimensions by default.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Add the project root to sys.path so 'backend.db.mongo' can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.db.mongo import get_client

# Load environment variables
load_dotenv()

# Initialize OpenAI Client
# Note: OPENAI_API_KEY must be set in the environment
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def scrape_mock_data() -> list[dict]:
    """
    Returns a list of dictionaries simulating scraped Ontario regulatory data.
    """
    return [
        {
            "source_url": "https://example.com/ontario/nursing",
            "governing_body": "College of Nurses of Ontario (CNO)",
            "text_chunk": "To become a registered nurse in Ontario, you must complete an approved nursing program and pass the NCLEX-RN exam."
        },
        {
            "source_url": "https://example.com/ontario/engineering",
            "governing_body": "Professional Engineers Ontario (PEO)",
            "text_chunk": "Professional Engineers in Ontario must have an accredited engineering degree and pass the Professional Practice Examination (PPE)."
        },
        {
            "source_url": "https://example.com/ontario/teaching",
            "governing_body": "Ontario College of Teachers (OCT)",
            "text_chunk": "Teachers in Ontario require a bachelor's degree and an acceptable teacher education program, followed by certification."
        }
    ]

async def process_and_store_documents():
    """
    Iterates over the mock data, generates embeddings, and inserts them into MongoDB.
    """
    mock_data = scrape_mock_data()
    
    # Connect to MongoDB using existing client logic
    mongo_client = get_client()
    db = mongo_client["roadmap_ontario"]
    collection = db["regulatory_docs"]
    
    print(f"Found {len(mock_data)} documents to process.")
    
    for doc in mock_data:
        governing_body = doc.get("governing_body", "Unknown")
        print(f"Processing chunk for {governing_body}...")
        
        # Generate embedding for the text chunk
        response = await openai_client.embeddings.create(
            input=doc["text_chunk"],
            model="text-embedding-3-small"
        )
        
        embedding = response.data[0].embedding
        
        # Append the generated embedding to the document
        doc["embedding"] = embedding
        
        # Insert the document into the regulatory_docs collection
        await collection.insert_one(doc)
        print(f"Successfully inserted document for {governing_body}.")

async def main():
    await process_and_store_documents()
    print("Data ingestion pipeline complete.")

if __name__ == "__main__":
    # Run the main async pipeline
    asyncio.run(main())
