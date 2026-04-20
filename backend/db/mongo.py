import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

_client: AsyncIOMotorClient = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _client = AsyncIOMotorClient(mongo_uri)
    return _client


def get_collection():
    client = get_client()
    db = client["roadmap_ontario"]
    return db["roadmaps"]


async def save_roadmap(request_id: str, data: dict) -> None:
    """Upsert a roadmap document indexed by request_id."""
    collection = get_collection()
    await collection.update_one(
        {"request_id": request_id},
        {"$set": data},
        upsert=True,
    )


async def get_roadmap(request_id: str) -> dict | None:
    """Fetch a roadmap document by request_id."""
    collection = get_collection()
    doc = await collection.find_one({"request_id": request_id}, {"_id": 0})
    return doc


async def update_status(request_id: str, status: str, error: str = None) -> None:
    """Update only the status (and optionally error) of a roadmap document."""
    collection = get_collection()
    update = {"status": status}
    if error:
        update["error"] = error
    await collection.update_one(
        {"request_id": request_id},
        {"$set": update},
    )
