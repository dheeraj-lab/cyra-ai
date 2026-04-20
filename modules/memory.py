import chromadb
from chromadb.utils import embedding_functions
import os
from datetime import datetime

MEMORY_PATH = "./memories"

client = chromadb.PersistentClient(path=MEMORY_PATH)

embedding_fn = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text"
)

collection = client.get_or_create_collection(
    name="cyra_memories",
    embedding_function=embedding_fn
)

def should_save_memory(text):
    """Filter out trivial messages that shouldn't be stored in long-term memory."""
    trivial_words = {"hi", "hello", "hey", "ok", "okay", "thanks", "thank you", "bye", "goodbye", "cyra", "siri"}
    words = set(text.lower().split())
    
    # Don't save if it's too short or just trivial words
    if len(words) < 4:
        return False
    if words.issubset(trivial_words):
        return False
    return True

def save_memory(text, memory_type="conversation"):
    if not should_save_memory(text):
        return
        
    try:
        timestamp = datetime.now().isoformat()
        memory_id = f"mem_{datetime.now().timestamp()}"
        collection.add(
            documents=[text],
            metadatas=[{"type": memory_type, "timestamp": timestamp}],
            ids=[memory_id]
        )
    except Exception as e:
        print(f"[Memory] Could not save: {e}")

def get_relevant_memories(query, n=3):
    try:
        count = collection.count()
        if count == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(n, count)
        )

        if results and results["documents"]:
            return results["documents"][0]
    except Exception as e:
        print(f"[Memory] Query failed: {e}")
    return []

def build_memory_context(query):
    memories = get_relevant_memories(query)
    if not memories:
        return ""

    context = "Relevant past facts you remember:\n"
    for mem in memories:
        # Avoid redundant context lines
        if mem.strip():
            context += f"- {mem}\n"
    return context