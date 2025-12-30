import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import os
from app.config import settings
from app.services.gemini_service import generate_embedding

logger = logging.getLogger(__name__)

# Initialize Qdrant client
def get_qdrant_client():
    """Get Qdrant client - supports embedded, local, and cloud modes"""
    if settings.QDRANT_USE_CLOUD:
        # Qdrant Cloud - requires URL and API key
        if not settings.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is required when using Qdrant Cloud")
        return QdrantClient(
            url=settings.QDRANT_HOST,  # Cloud URL format: https://xxx.qdrant.io
            api_key=settings.QDRANT_API_KEY
        )
    elif settings.QDRANT_HOST == "localhost" or settings.QDRANT_HOST == "127.0.0.1":
        # Try embedded mode for localhost
        try:
            return QdrantClient(path="./qdrant_storage")
        except:
            # Fallback to local connection
            port = settings.QDRANT_PORT if settings.QDRANT_PORT else 6333
            return QdrantClient(host=settings.QDRANT_HOST, port=port)
    else:
        # Remote Qdrant instance
        port = settings.QDRANT_PORT if settings.QDRANT_PORT else 6333
        if settings.QDRANT_API_KEY:
            # If API key provided, use it for authentication
            return QdrantClient(
                host=settings.QDRANT_HOST,
                port=port,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            return QdrantClient(host=settings.QDRANT_HOST, port=port)

qdrant_client = get_qdrant_client()


def initialize_qdrant_collection(collection_name: str = None, vector_size: int = None):
    """Initialize Qdrant collection for HR policies"""
    if collection_name is None:
        collection_name = settings.QDRANT_COLLECTION_NAME
    
    # Use configured size or default
    if vector_size is None:
        vector_size = settings.QDRANT_VECTOR_SIZE if settings.QDRANT_VECTOR_SIZE else 768
    
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            # Create collection with specified dimensions
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"Created Qdrant collection: {collection_name} with {vector_size} dimensions")
        else:
            # Check if existing collection has correct dimension
            collection_info = qdrant_client.get_collection(collection_name)
            existing_size = collection_info.config.params.vectors.size
            
            if existing_size != vector_size:
                print(f"Warning: Collection {collection_name} exists with {existing_size} dimensions, but expected {vector_size}")
                print(f"Deleting existing collection and recreating with {vector_size} dimensions...")
                qdrant_client.delete_collection(collection_name)
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                print(f"Recreated Qdrant collection: {collection_name} with {vector_size} dimensions")
            else:
                print(f"Qdrant collection {collection_name} already exists with {vector_size} dimensions")
    except Exception as e:
        print(f"Error initializing Qdrant collection: {e}")
        raise


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into chunks with overlap"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks


def ingest_policy_documents(policies_dir: str = "app/data/hr_policies"):
    """Ingest HR policy documents into Qdrant"""
    collection_name = settings.QDRANT_COLLECTION_NAME
    
    # First, detect embedding dimension by generating a test embedding
    print("Detecting embedding dimension...")
    test_embedding = generate_embedding("test")
    if not test_embedding:
        raise ValueError("Failed to generate test embedding. Check your GEMINI_API_KEY and GEMINI_EMBEDDING_MODEL.")
    
    vector_size = len(test_embedding)
    print(f"Detected embedding dimension: {vector_size}")
    
    # Initialize collection with detected dimension
    initialize_qdrant_collection(collection_name, vector_size)
    
    points = []
    point_id = 0
    
    # Get all .txt files in policies directory
    policies_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), policies_dir)
    
    if not os.path.exists(policies_path):
        print(f"Policies directory not found: {policies_path}")
        return
    
    for filename in os.listdir(policies_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(policies_path, filename)
            policy_name = filename.replace('.txt', '').replace('_', ' ').title()
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chunk the content
            chunks = chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = generate_embedding(chunk)
                
                if not embedding:
                    print(f"Warning: Failed to generate embedding for chunk {i} of {filename}, skipping...")
                    continue
                
                # Verify dimension matches
                if len(embedding) != vector_size:
                    print(f"Warning: Embedding dimension mismatch. Expected {vector_size}, got {len(embedding)}")
                    continue
                
                # Create point with metadata
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "policy_name": policy_name,
                        "chunk_index": i,
                        "text": chunk,
                        "filename": filename
                    }
                )
                points.append(point)
                point_id += 1
    
    # Upsert points to Qdrant
    if points:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Ingested {len(points)} chunks from policy documents")


def search_policies(query: str, top_k: int = 3) -> List[Dict]:
    """Search for relevant policy chunks"""
    logger.info(f"🔍 RAG: Searching policies for query: '{query[:100]}...'")
    collection_name = settings.QDRANT_COLLECTION_NAME
    
    # Generate query embedding
    logger.info("   Generating query embedding...")
    query_embedding = generate_embedding(query)
    
    if not query_embedding:
        logger.warning("   ✗ Failed to generate query embedding")
        return []
    
    logger.info(f"   ✓ Embedding generated: {len(query_embedding)} dimensions")
    
    # Search in Qdrant - use the search method (works with all versions)
    try:
        logger.info(f"   Searching Qdrant collection '{collection_name}' (top_k={top_k})...")
        # Use the standard search method which works with all Qdrant versions
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        logger.info(f"   ✓ Found {len(results)} results from Qdrant")
        
        # Format results
        chunks = []
        for idx, result in enumerate(results, 1):
            # Handle different result formats
            if hasattr(result, 'payload'):
                payload = result.payload if result.payload else {}
            elif hasattr(result, 'point') and hasattr(result.point, 'payload'):
                payload = result.point.payload if result.point.payload else {}
            else:
                payload = {}
            
            score = result.score if hasattr(result, 'score') else 0.0
            
            chunk_data = {
                "text": payload.get("text", ""),
                "policy_name": payload.get("policy_name", ""),
                "score": score
            }
            chunks.append(chunk_data)
            logger.info(f"   Result {idx}: {chunk_data['policy_name']} (score: {score:.4f})")
        
        logger.info(f"   ✓ Returning {len(chunks)} policy chunks")
        return chunks
            
    except AttributeError:
        # If search method doesn't exist, try query_points with correct parameters
        try:
            results = qdrant_client.query_points(
                collection_name=collection_name,
                query=query_embedding,  # Pass vector directly
                limit=top_k  # Use 'limit' instead of 'top'
            )
            
            chunks = []
            if hasattr(results, 'points'):
                for point in results.points:
                    payload = point.payload if hasattr(point, 'payload') and point.payload else {}
                    score = point.score if hasattr(point, 'score') else 0.0
                    chunks.append({
                        "text": payload.get("text", ""),
                        "policy_name": payload.get("policy_name", ""),
                        "score": score
                    })
            return chunks
        except Exception as e2:
            print(f"Error with query_points: {e2}")
            # If both methods fail, return empty list
            return []
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_rag_context(query: str, top_k: int = 3) -> str:
    """Get RAG context for a query"""
    chunks = search_policies(query, top_k)
    
    if not chunks:
        logger.warning("   No chunks found, returning empty context")
        return ""
    
    context_parts = []
    for chunk in chunks:
        context_parts.append(f"[From {chunk['policy_name']}]\n{chunk['text']}\n")
    
    context = "\n".join(context_parts)
    logger.info(f"   ✓ RAG context assembled: {len(context)} characters from {len(chunks)} chunks")
    return context

