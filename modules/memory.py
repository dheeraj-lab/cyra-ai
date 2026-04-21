import os
import chromadb
from sentence_transformers import SentenceTransformer
import datetime

# Initialize ChromaDB
DB_PATH = "memories/chroma_db"
os.makedirs("memories", exist_ok=True)

client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="cyra_long_term_memory")

# Load a small, fast embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

def save_memory(text, metadata=None):
    """Save a piece of information to long-term memory."""
    if not text or len(text.strip()) < 5:
        return
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    embedding = model.encode(text).tolist()
    
    collection.add(
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata or {"timestamp": timestamp}],
        ids=[f"mem_{int(datetime.datetime.now().timestamp() * 1000)}"]
    )
    # print(f"[Memory] Saved: {text[:50]}...")

def build_memory_context(query, n_results=5):
    """Retrieve relevant memories for the current query."""
    if not query:
        return ""
    
    try:
        query_embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        memories = results.get("documents", [[]])[0]
        if not memories:
            return ""
        
        context = "\nThings you remember that might be relevant:\n"
        for i, mem in enumerate(memories, 1):
            context += f"- {mem}\n"
        return context
    except Exception as e:
        print(f"[Memory] Retrieval error: {e}")
        return ""

def forget_everything():
    """Clear all memories."""
    client.delete_collection("cyra_long_term_memory")
    global collection
    collection = client.get_or_create_collection(name="cyra_long_term_memory")
    return "Everything forgotten!"