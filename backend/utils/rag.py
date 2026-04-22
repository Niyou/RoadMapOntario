async def retrieve_context(profession: str, top_k: int = 3) -> str:
    """
    Retrieves relevant regulatory context for a given profession.
    Currently mocked to rely on LLM training data since MongoDB has been removed.
    """
    return "No local vector database configured. Rely entirely on your training data."
