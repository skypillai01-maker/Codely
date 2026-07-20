import os
import faiss
import numpy as np
import pickle
import logging
import threading
from typing import List, Dict, Any, Optional, Callable
from core.memory.base import BaseMemory
from core.config import BATCH_EMBED_SIZE

logger = logging.getLogger(__name__)

# HNSW parameters (same as video - production grade)
HNSW_M = 32  # Number of bi-directional links per node
HNSW_EF_CONSTRUCTION = 200  # Build-time search width
HNSW_EF_SEARCH = 50  # Query-time search width

# Chunking parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

class FAISSVectorStore(BaseMemory):
    def __init__(self, embed_adapter, base_path: str = "storage/memory", user_id: str = None):
        self.embed_adapter = embed_adapter
        self.user_id = user_id
        self.base_path = os.path.join(base_path, user_id) if user_id else base_path
        self._index_cache = {}
        self._meta_cache = {}
        self._cache_lock = threading.Lock()
        os.makedirs(self.base_path, exist_ok=True)

    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks for embedding."""
        if len(text) <= CHUNK_SIZE:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunks.append(text[start:end])
            start += CHUNK_SIZE - CHUNK_OVERLAP
            if start >= len(text):
                break
        return chunks

    def _get_context_path(self, context_id: str) -> str:
        path = os.path.join(self.base_path, context_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _load_index(self, context_id: str):
        # Check cache first (thread-safe)
        with self._cache_lock:
            if context_id in self._index_cache:
                return self._index_cache[context_id], self._meta_cache[context_id]

        path = self._get_context_path(context_id)
        index_file = os.path.join(path, "index.faiss")
        meta_file = os.path.join(path, "metadata.pkl")

        if os.path.exists(index_file) and os.path.exists(meta_file):
            index = faiss.read_index(index_file)
            with open(meta_file, "rb") as f:
                metadata = pickle.load(f)
            
            # Update cache (thread-safe)
            with self._cache_lock:
                self._index_cache[context_id] = index
                self._meta_cache[context_id] = metadata
            return index, metadata
            
        return None, []

    def _save_index(self, context_id: str, index, metadata):
        path = self._get_context_path(context_id)
        faiss.write_index(index, os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "metadata.pkl"), "wb") as f:
            pickle.dump(metadata, f)
        
        # Update cache (thread-safe)
        with self._cache_lock:
            self._index_cache[context_id] = index
            self._meta_cache[context_id] = metadata

    def add(self, context_id: str, text: str, metadata: Dict[str, Any] = None, progress_callback: Callable = None):
        try:
            import hashlib
            from datetime import datetime
            
            # Split text into chunks
            chunks = self._split_text(text)
            if not chunks:
                return

            # Generate doc_id, source, timestamp for the document
            doc_metadata = metadata or {}
            if "doc_id" not in doc_metadata:
                # Generate doc_id from text and current time
                doc_id = hashlib.md5(f"{text[:1000]}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
                doc_metadata["doc_id"] = doc_id
            if "source" not in doc_metadata:
                doc_metadata["source"] = f"context_{context_id}"
            if "timestamp" not in doc_metadata:
                doc_metadata["timestamp"] = datetime.now().isoformat()

            # Generate embeddings in batches
            embeddings = []
            total_chunks = len(chunks)
            
            for i in range(0, total_chunks, BATCH_EMBED_SIZE):
                batch = chunks[i:i + BATCH_EMBED_SIZE]
                for j, chunk in enumerate(batch):
                    embedding = self.embed_adapter.embed(chunk)
                    if embedding:
                        embeddings.append((chunk, embedding))
                    if progress_callback:
                        progress = int(((i + j + 1) / total_chunks) * 80) + 10
                        progress_callback(progress, f"Embedding chunk {i + j + 1}/{total_chunks}")
                
            if not embeddings:
                logger.warning(f"No valid embeddings for context_id={context_id}")
                return

            index, existing_metadata = self._load_index(context_id)

            # Create HNSW index if new context (same algorithm as the video)
            if index is None:
                dimension = len(embeddings[0][1])
                index = faiss.IndexHNSWFlat(dimension, HNSW_M)
                index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
                index.hnsw.efSearch = HNSW_EF_SEARCH

            # Add all chunk embeddings
            if progress_callback:
                progress_callback(90, "Adding embeddings to index")
            
            for chunk_text, embedding in embeddings:
                embedding_np = np.array([embedding]).astype('float32')
                index.add(embedding_np)
                chunk_metadata = {
                    "text": chunk_text,
                    "metadata": doc_metadata,
                    "chunk_index": len(existing_metadata)
                }
                existing_metadata.append(chunk_metadata)

            self._save_index(context_id, index, existing_metadata)
            logger.debug(f"Added {len(embeddings)} chunks to context_id={context_id}, total={len(existing_metadata)}")
            if progress_callback:
                progress_callback(100, "Complete")

        except Exception as e:
            logger.error(f"Failed to add to memory context_id={context_id}: {type(e).__name__}: {e}")

    def search(self, context_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            index, metadata = self._load_index(context_id)
            if index is None or not metadata:
                return []

            query_embedding = self.embed_adapter.embed(query)
            if not query_embedding:
                logger.warning(f"Empty embedding for query in context_id={context_id}")
                return []
                
            query_np = np.array([query_embedding]).astype('float32')
            
            distances, indices = index.search(query_np, min(limit, len(metadata)))
            
            results = []
            for i in indices[0]:
                if i != -1 and i < len(metadata):
                    results.append(metadata[i])
            return results
        except Exception as e:
            logger.error(f"Search failed for context_id={context_id}: {type(e).__name__}: {e}")
            return []

    def clear(self, context_id: str):
        import shutil
        path = self._get_context_path(context_id)
        if os.path.exists(path):
            shutil.rmtree(path)
        
        # Clear cache (thread-safe)
        with self._cache_lock:
            if context_id in self._index_cache:
                del self._index_cache[context_id]
            if context_id in self._meta_cache:
                del self._meta_cache[context_id]

    def merge(self, target_context_id: str, source_context_ids: List[str]) -> int:
        """Merge memory from multiple source contexts into a target context."""
        entries_merged = 0

        # Load or create target index with HNSW
        target_index, target_metadata = self._load_index(target_context_id)

        if target_index is None:
            # Will be created when first chunk is added
            target_index = None
            target_metadata = []

        for source_id in source_context_ids:
            source_index, source_metadata = self._load_index(source_id)

            if source_index is None or not source_metadata:
                continue

            # If target doesn't exist yet, use source as base
            if target_index is None and source_index.ntotal > 0:
                dimension = source_index.d
                target_index = faiss.IndexHNSWFlat(dimension, HNSW_M)
                target_index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
                target_index.hnsw.efSearch = HNSW_EF_SEARCH

            if target_index is not None:
                try:
                    # Copy vectors from source to target
                    for i, meta in enumerate(source_metadata):
                        # Get the vector from source
                        vec = source_index.reconstruct(i)
                        target_index.add(np.array([vec]))
                        target_metadata.append(meta)

                    entries_merged += len(source_metadata)

                except Exception as e:
                    logger.error(f"Failed to merge from {source_id} to {target_context_id}: {e}")
                    continue

        if target_index is not None and entries_merged > 0:
            self._save_index(target_context_id, target_index, target_metadata)

        return entries_merged

    def get_stats(self, context_id: str) -> Dict[str, Any]:
        """Get statistics for a context."""
        path = self._get_context_path(context_id)
        index_file = os.path.join(path, "index.faiss")
        meta_file = os.path.join(path, "metadata.pkl")
        
        entries = 0
        size = 0
        
        if os.path.exists(meta_file):
            with open(meta_file, "rb") as f:
                metadata = pickle.load(f)
                entries = len(metadata)
        
        if os.path.exists(index_file):
            size = os.path.getsize(index_file)
        
        return {
            "context_id": context_id,
            "entries": entries,
            "size_bytes": size,
            "exists": os.path.exists(path)
        }

    def list_contexts(self) -> List[str]:
        """List all existing context IDs."""
        contexts = []
        if os.path.exists(self.base_path):
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path):
                    contexts.append(item)
        return contexts
        
    def list_documents(self, context_id: str) -> List[Dict[str, Any]]:
        """List all ingested documents for a context."""
        _, metadata = self._load_index(context_id)
        if not metadata:
            return []
            
        # Group by doc_id and get unique documents
        docs = {}
        for chunk in metadata:
            doc_meta = chunk.get("metadata", {})
            doc_id = doc_meta.get("doc_id")
            if doc_id and doc_id not in docs:
                # Already have this doc, just update
                docs[doc_id]["chunk_count"] += 1
            elif doc_id:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "source": doc_meta.get("source"),
                    "timestamp": doc_meta.get("timestamp"),
                    "chunk_count": 1
                }
        return list(docs.values())
        
    def delete_document(self, context_id: str, doc_id: str) -> bool:
        """Delete a document by doc_id, rebuilding the HNSW index."""
        index, metadata = self._load_index(context_id)
        if index is None or not metadata:
            return False
            
        # Filter out chunks with this doc_id
        kept_chunks = []
        for chunk in metadata:
            if chunk.get("metadata", {}).get("doc_id") != doc_id:
                kept_chunks.append(chunk)
                
        if len(kept_chunks) == len(metadata):
            # No chunks were removed
            return False
            
        # Rebuild index with kept chunks
        if kept_chunks:
            # Need to get embeddings for kept chunks
            # Re-embed or reconstruct vectors? Wait, we can reconstruct from old index!
            dimension = index.d
            new_index = faiss.IndexHNSWFlat(dimension, HNSW_M)
            new_index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
            new_index.hnsw.efSearch = HNSW_EF_SEARCH
            
            # Reconstruct vectors from old index and add to new index
            new_metadata = []
            for i, chunk in enumerate(metadata):
                if chunk.get("metadata", {}).get("doc_id") != doc_id:
                    vec = index.reconstruct(i)
                    new_index.add(np.array([vec]))
                    # Update chunk_index to new index
                    chunk["chunk_index"] = len(new_metadata)
                    new_metadata.append(chunk)
                    
            self._save_index(context_id, new_index, new_metadata)
        else:
            # No chunks left, clear the context
            self.clear(context_id)
            
        logger.info(f"Deleted document doc_id={doc_id} from context_id={context_id}")
        return True
