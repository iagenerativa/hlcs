"""
Knowledge RAG System for HLCS AGI

Semantic retrieval with ChromaDB persistence and hierarchical memory.
Separates storage (ChromaDB), embedding (all-MiniLM-L6-v2), and generation (local LLM).

Architecture:
- Storage: ChromaDB on disk for persistence
- Embedding: all-MiniLM-L6-v2 (~50MB, fast queries)
- Generation: External LLM (Phi4-mini via llamafile)
- Orchestration: LangChain (lightweight, minimal overhead)

Memory Hierarchy:
- Short-Term Memory (STM): Recent interactions with TTL
- Long-Term Memory (LTM): Consolidated knowledge with high relevance
- Auto-promotion: STM → LTM based on access frequency and importance

Metadata for Semantic Filtering:
- knowledge_type: episodic, semantic, procedural
- memory_tier: short_term, long_term
- timestamp: ISO format for temporal filtering
- source: Origin of knowledge (user, system, external)
- confidence_score: 0-1 reliability score
- access_count: Usage tracking for consolidation

Version: 2.0.0 (ChromaDB + Hierarchical Memory)
"""

import logging
from typing import List, Dict, Any, Optional, Literal
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not installed, embeddings will use mock")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb not installed, falling back to in-memory storage")

try:
    from langchain_community.vectorstores import Chroma
    from langchain_core.documents import Document as LangChainDocument
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("langchain not installed, orchestration will be limited")


# Type aliases
KnowledgeType = Literal["episodic", "semantic", "procedural"]
MemoryTier = Literal["short_term", "long_term"]


@dataclass
class MemoryMetadata:
    """Metadata for memory vectors."""
    knowledge_type: KnowledgeType
    memory_tier: MemoryTier
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = "system"
    confidence_score: float = 1.0
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to ChromaDB-compatible dict."""
        return {
            "knowledge_type": self.knowledge_type,
            "memory_tier": self.memory_tier,
            "timestamp": self.timestamp,
            "source": self.source,
            "confidence_score": self.confidence_score,
            "access_count": self.access_count,
            "tags": json.dumps(self.tags)  # ChromaDB doesn't support lists in metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryMetadata":
        """Create from ChromaDB metadata dict."""
        tags = json.loads(data.get("tags", "[]")) if isinstance(data.get("tags"), str) else data.get("tags", [])
        return cls(
            knowledge_type=data["knowledge_type"],
            memory_tier=data["memory_tier"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            source=data.get("source", "system"),
            confidence_score=float(data.get("confidence_score", 1.0)),
            access_count=int(data.get("access_count", 0)),
            tags=tags
        )


@dataclass
class RetrievalResult:
    """Result from RAG retrieval."""
    content: str
    metadata: MemoryMetadata
    score: float
    id: str


@dataclass
class RetrievalResult:
    """Result from RAG retrieval."""
    content: str
    metadata: MemoryMetadata
    score: float
    id: str


class KnowledgeRAG:
    """
    RAG system with ChromaDB persistence and hierarchical memory.
    
    Features:
    - Persistent storage via ChromaDB (disk-based)
    - Semantic search with all-MiniLM-L6-v2 (50MB, fast)
    - Hierarchical memory (short-term ↔ long-term)
    - Rich metadata for semantic filtering
    - Auto-consolidation of frequent knowledge
    - LangChain integration for orchestration
    
    Architecture:
        Query → Embedding → ChromaDB Search → Metadata Filter → Reranking → Results
        
    Memory Tiers:
        - Short-Term: Recent interactions, auto-expire after TTL
        - Long-Term: Consolidated knowledge, high access count
        
    Example:
        >>> rag = KnowledgeRAG(persist_dir="./data/chroma_db")
        >>> rag.add_memory(
        ...     "User prefers Python over JavaScript",
        ...     metadata=MemoryMetadata(knowledge_type="episodic", memory_tier="short_term")
        ... )
        >>> results = rag.retrieve("What language does user prefer?", top_k=3)
        >>> for res in results:
        ...     print(f"{res.content} (score: {res.score:.3f})")
    """
    
    def __init__(
        self,
        persist_dir: str = "./data/chroma_db",
        collection_name: str = "hlcs_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2",
        stm_ttl_hours: int = 24,
        ltm_promotion_threshold: int = 3
    ):
        """
        Initialize RAG with ChromaDB backend.
        
        Args:
            persist_dir: Directory for ChromaDB persistence
            collection_name: Name of ChromaDB collection
            embedding_model: Sentence transformer model name
            stm_ttl_hours: TTL for short-term memories (hours)
            ltm_promotion_threshold: Access count for STM → LTM promotion
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.stm_ttl_hours = stm_ttl_hours
        self.ltm_promotion_threshold = ltm_promotion_threshold
        
        # Initialize embedding model
        if EMBEDDINGS_AVAILABLE:
            self.encoder = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
        else:
            self.encoder = None
            logger.warning("Running without embeddings (mock mode)")
        
        # Initialize mock storage (always, as fallback)
        self._mock_storage: List[Dict[str, Any]] = []
        
        # Initialize ChromaDB
        if CHROMADB_AVAILABLE:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )
            logger.info(f"ChromaDB initialized at {persist_dir} with {self.collection.count()} vectors")
        else:
            self.chroma_client = None
            self.collection = None
            logger.warning("Running without ChromaDB (in-memory mock)")
        
        # LangChain integration (if available)
        self.langchain_vectorstore = None
        if LANGCHAIN_AVAILABLE and CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE:
            try:
                self.langchain_vectorstore = Chroma(
                    client=self.chroma_client,
                    collection_name=collection_name,
                    embedding_function=self._get_langchain_embedding_function()
                )
                logger.info("LangChain VectorStore initialized")
            except Exception as e:
                logger.warning(f"Could not initialize LangChain VectorStore: {e}")
    
    def _get_langchain_embedding_function(self):
        """Get LangChain-compatible embedding function."""
        if not EMBEDDINGS_AVAILABLE:
            return None
        
        class SentenceTransformerEmbeddings:
            def __init__(self, model):
                self.model = model
            
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                return self.model.encode(texts, show_progress_bar=False).tolist()
            
            def embed_query(self, text: str) -> List[float]:
                return self.model.encode(text, show_progress_bar=False).tolist()
        
        return SentenceTransformerEmbeddings(self.encoder)
    
    def add_memory(
        self,
        content: str,
        metadata: Optional[MemoryMetadata] = None,
        id: Optional[str] = None
    ) -> str:
        """
        Add memory to RAG system.
        
        Args:
            content: Text content to store
            metadata: Memory metadata (auto-created if None)
            id: Optional custom ID (auto-generated if None)
        
        Returns:
            Memory ID
        """
        if not content.strip():
            raise ValueError("Cannot add empty content")
        
        # Create default metadata if not provided
        if metadata is None:
            metadata = MemoryMetadata(
                knowledge_type="semantic",
                memory_tier="short_term"
            )
        
        # Generate ID if not provided
        if id is None:
            id = f"mem_{datetime.utcnow().timestamp()}"
        
        # Compute embedding
        if EMBEDDINGS_AVAILABLE and self.encoder:
            embedding = self.encoder.encode(content, show_progress_bar=False).tolist()
        else:
            # Mock embedding
            embedding = [0.1] * 384  # MiniLM dimension
        
        # Store in ChromaDB
        if CHROMADB_AVAILABLE and self.collection:
            try:
                self.collection.add(
                    ids=[id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata.to_dict()]
                )
                logger.debug(f"Added memory {id} to ChromaDB")
            except Exception as e:
                logger.error(f"Error adding to ChromaDB: {e}")
                raise
        else:
            # Mock storage
            self._mock_storage.append({
                "id": id,
                "content": content,
                "metadata": metadata.to_dict(),
                "embedding": embedding
            })
            logger.debug(f"Added memory {id} to mock storage")
        
        return id
    
    def add_memories_bulk(
        self,
        contents: List[str],
        metadatas: Optional[List[MemoryMetadata]] = None
    ) -> List[str]:
        """
        Add multiple memories efficiently.
        
        Args:
            contents: List of text contents
            metadatas: List of metadata (auto-created if None)
        
        Returns:
            List of memory IDs
        """
        if not contents:
            return []
        
        # Create default metadatas if not provided
        if metadatas is None:
            metadatas = [
                MemoryMetadata(knowledge_type="semantic", memory_tier="short_term")
                for _ in contents
            ]
        
        if len(metadatas) != len(contents):
            raise ValueError("metadatas length must match contents length")
        
        # Generate IDs
        ids = [f"mem_{datetime.utcnow().timestamp()}_{i}" for i in range(len(contents))]
        
        # Compute embeddings
        if EMBEDDINGS_AVAILABLE and self.encoder:
            embeddings = self.encoder.encode(contents, show_progress_bar=False).tolist()
        else:
            embeddings = [[0.1] * 384 for _ in contents]
        
        # Store in ChromaDB
        if CHROMADB_AVAILABLE and self.collection:
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=contents,
                    metadatas=[m.to_dict() for m in metadatas]
                )
                logger.info(f"Added {len(ids)} memories to ChromaDB")
            except Exception as e:
                logger.error(f"Error adding bulk to ChromaDB: {e}")
                raise
        else:
            # Mock storage
            for id, content, metadata, embedding in zip(ids, contents, metadatas, embeddings):
                self._mock_storage.append({
                    "id": id,
                    "content": content,
                    "metadata": metadata.to_dict(),
                    "embedding": embedding
                })
            logger.info(f"Added {len(ids)} memories to mock storage")
        
        return ids
    
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        knowledge_type: Optional[KnowledgeType] = None,
        memory_tier: Optional[MemoryTier] = None,
        min_confidence: float = 0.0,
        tags: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve most relevant memories for query.
        
        Uses semantic similarity + metadata filtering + reranking.
        
        Args:
            query: Query text
            top_k: Number of results to return
            knowledge_type: Filter by knowledge type
            memory_tier: Filter by memory tier
            min_confidence: Minimum confidence score
            tags: Filter by tags (any match)
        
        Returns:
            List of RetrievalResult objects (ordered by relevance)
        """
        if not query.strip():
            return []
        
        # Build metadata filter for ChromaDB
        where_filter = {}
        if knowledge_type:
            where_filter["knowledge_type"] = knowledge_type
        if memory_tier:
            where_filter["memory_tier"] = memory_tier
        if min_confidence > 0:
            where_filter["confidence_score"] = {"$gte": min_confidence}
        
        # Retrieve from ChromaDB
        if CHROMADB_AVAILABLE and self.collection and EMBEDDINGS_AVAILABLE and self.encoder:
            try:
                # Encode query
                query_embedding = self.encoder.encode(query, show_progress_bar=False).tolist()
                
                # Query ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k * 2,  # Get extra for reranking
                    where=where_filter if where_filter else None
                )
                
                # Update access counts (for consolidation)
                if results["ids"] and results["ids"][0]:
                    for mem_id in results["ids"][0]:
                        self._increment_access_count(mem_id)
                
                # Convert to RetrievalResult
                retrieval_results = []
                if results["ids"] and results["ids"][0]:
                    for idx, mem_id in enumerate(results["ids"][0]):
                        content = results["documents"][0][idx]
                        metadata_dict = results["metadatas"][0][idx]
                        distance = results["distances"][0][idx] if "distances" in results else 0.0
                        
                        # Convert distance to similarity score (cosine: 0=identical, 2=opposite)
                        score = 1.0 - (distance / 2.0)
                        
                        metadata = MemoryMetadata.from_dict(metadata_dict)
                        
                        # Tag filtering (post-filter since ChromaDB doesn't support list queries)
                        if tags:
                            mem_tags = set(metadata.tags)
                            if not mem_tags.intersection(set(tags)):
                                continue  # Skip if no tag match
                        
                        retrieval_results.append(RetrievalResult(
                            content=content,
                            metadata=metadata,
                            score=score,
                            id=mem_id
                        ))
                
                # Reranking: boost by confidence and recency
                reranked = self._rerank_results(retrieval_results)
                
                return reranked[:top_k]
                
            except Exception as e:
                logger.error(f"Retrieval error: {e}")
                return []
        else:
            # Mock retrieval from in-memory storage
            logger.warning("Using mock retrieval")
            mock_results = []
            for item in self._mock_storage[:top_k]:
                metadata = MemoryMetadata.from_dict(item["metadata"])
                mock_results.append(RetrievalResult(
                    content=item["content"],
                    metadata=metadata,
                    score=0.9,  # Mock score
                    id=item["id"]
                ))
            return mock_results
    
    def _rerank_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Rerank results by combining semantic score, confidence, and recency.
        
        Formula: final_score = semantic_score * confidence * recency_factor
        """
        if not results:
            return []
        
        now = datetime.utcnow()
        reranked = []
        
        for result in results:
            # Parse timestamp
            try:
                mem_time = datetime.fromisoformat(result.metadata.timestamp.replace('Z', '+00:00'))
                hours_old = (now - mem_time).total_seconds() / 3600
                # Recency factor: 1.0 for fresh, decays to 0.5 over 7 days
                recency_factor = max(0.5, 1.0 - (hours_old / (7 * 24)))
            except Exception:
                recency_factor = 0.7  # Default if timestamp invalid
            
            # Combine factors
            final_score = (
                result.score *
                result.metadata.confidence_score *
                recency_factor
            )
            
            reranked.append((result, final_score))
        
        # Sort by final score
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        # Return results with updated scores
        return [
            RetrievalResult(
                content=r.content,
                metadata=r.metadata,
                score=final_score,
                id=r.id
            )
            for r, final_score in reranked
        ]
    
    def _increment_access_count(self, mem_id: str):
        """Increment access count for memory (used for STM→LTM promotion)."""
        if not (CHROMADB_AVAILABLE and self.collection):
            return
        
        try:
            # Get current metadata
            result = self.collection.get(ids=[mem_id], include=["metadatas"])
            if not result["metadatas"]:
                return
            
            metadata_dict = result["metadatas"][0]
            metadata_dict["access_count"] = int(metadata_dict.get("access_count", 0)) + 1
            
            # Check for STM→LTM promotion
            if (metadata_dict["memory_tier"] == "short_term" and
                metadata_dict["access_count"] >= self.ltm_promotion_threshold):
                metadata_dict["memory_tier"] = "long_term"
                logger.info(f"Promoted {mem_id} from STM to LTM (access_count={metadata_dict['access_count']})")
            
            # Update metadata
            self.collection.update(
                ids=[mem_id],
                metadatas=[metadata_dict]
            )
        except Exception as e:
            logger.error(f"Error incrementing access count: {e}")
    
    def consolidate_memories(self) -> Dict[str, int]:
        """
        Consolidate short-term memories to long-term.
        
        Promotes STM → LTM based on:
        - Access count >= threshold
        - High confidence score
        - Semantic importance (future: clustering)
        
        Returns:
            Stats dict with promotion counts
        """
        if not (CHROMADB_AVAILABLE and self.collection):
            logger.warning("Cannot consolidate without ChromaDB")
            return {"promoted": 0, "expired": 0}
        
        try:
            # Get all short-term memories
            stm_results = self.collection.get(
                where={"memory_tier": "short_term"},
                include=["metadatas"]
            )
            
            promoted_count = 0
            expired_ids = []
            
            now = datetime.utcnow()
            
            for mem_id, metadata_dict in zip(stm_results["ids"], stm_results["metadatas"]):
                # Check for promotion
                access_count = int(metadata_dict.get("access_count", 0))
                confidence = float(metadata_dict.get("confidence_score", 0.0))
                
                if access_count >= self.ltm_promotion_threshold or confidence >= 0.9:
                    # Promote to LTM
                    metadata_dict["memory_tier"] = "long_term"
                    self.collection.update(
                        ids=[mem_id],
                        metadatas=[metadata_dict]
                    )
                    promoted_count += 1
                    logger.debug(f"Promoted {mem_id} to LTM")
                else:
                    # Check for expiration
                    try:
                        mem_time = datetime.fromisoformat(metadata_dict["timestamp"].replace('Z', '+00:00'))
                        hours_old = (now - mem_time).total_seconds() / 3600
                        
                        if hours_old > self.stm_ttl_hours:
                            expired_ids.append(mem_id)
                    except Exception as e:
                        logger.warning(f"Could not parse timestamp for {mem_id}: {e}")
            
            # Delete expired STM
            if expired_ids:
                self.collection.delete(ids=expired_ids)
                logger.info(f"Deleted {len(expired_ids)} expired STM entries")
            
            logger.info(f"Consolidation: promoted {promoted_count}, expired {len(expired_ids)}")
            return {"promoted": promoted_count, "expired": len(expired_ids)}
            
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}")
            return {"promoted": 0, "expired": 0}
    
    def search_by_metadata(
        self,
        knowledge_type: Optional[KnowledgeType] = None,
        memory_tier: Optional[MemoryTier] = None,
        source: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[RetrievalResult]:
        """
        Search memories by metadata only (no semantic search).
        
        Useful for browsing specific memory categories.
        
        Args:
            knowledge_type: Filter by knowledge type
            memory_tier: Filter by memory tier
            source: Filter by source
            min_confidence: Minimum confidence score
            limit: Maximum results
        
        Returns:
            List of matching memories
        """
        if not (CHROMADB_AVAILABLE and self.collection):
            return []
        
        # Build filter
        where_filter = {}
        if knowledge_type:
            where_filter["knowledge_type"] = knowledge_type
        if memory_tier:
            where_filter["memory_tier"] = memory_tier
        if source:
            where_filter["source"] = source
        if min_confidence > 0:
            where_filter["confidence_score"] = {"$gte": min_confidence}
        
        try:
            results = self.collection.get(
                where=where_filter if where_filter else None,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            retrieval_results = []
            if results["ids"]:
                for idx, mem_id in enumerate(results["ids"]):
                    content = results["documents"][idx]
                    metadata_dict = results["metadatas"][idx]
                    metadata = MemoryMetadata.from_dict(metadata_dict)
                    
                    retrieval_results.append(RetrievalResult(
                        content=content,
                        metadata=metadata,
                        score=1.0,  # No semantic scoring
                        id=mem_id
                    ))
            
            return retrieval_results
        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG system statistics.
        
        Returns:
            Stats dict with counts by tier, type, etc.
        """
        if not (CHROMADB_AVAILABLE and self.collection):
            return {
                "total_memories": len(self._mock_storage),
                "backend": "mock"
            }
        
        try:
            total = self.collection.count()
            
            # Count by memory tier
            stm_count = len(self.collection.get(
                where={"memory_tier": "short_term"},
                limit=10000  # Reasonable limit
            )["ids"])
            ltm_count = total - stm_count
            
            # Count by knowledge type
            episodic_count = len(self.collection.get(
                where={"knowledge_type": "episodic"},
                limit=10000
            )["ids"])
            semantic_count = len(self.collection.get(
                where={"knowledge_type": "semantic"},
                limit=10000
            )["ids"])
            procedural_count = total - episodic_count - semantic_count
            
            return {
                "total_memories": total,
                "short_term": stm_count,
                "long_term": ltm_count,
                "episodic": episodic_count,
                "semantic": semantic_count,
                "procedural": procedural_count,
                "backend": "chromadb",
                "persist_dir": str(self.persist_dir),
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def clear_all(self):
        """Clear all memories (use with caution!)."""
        if CHROMADB_AVAILABLE and self.collection:
            try:
                # Delete all documents
                all_ids = self.collection.get()["ids"]
                if all_ids:
                    self.collection.delete(ids=all_ids)
                logger.warning(f"Cleared {len(all_ids)} memories from ChromaDB")
            except Exception as e:
                logger.error(f"Error clearing ChromaDB: {e}")
        else:
            self._mock_storage.clear()
            logger.warning("Cleared mock storage")
    
    def delete_memory(self, mem_id: str):
        """Delete a specific memory."""
        if CHROMADB_AVAILABLE and self.collection:
            try:
                self.collection.delete(ids=[mem_id])
                logger.debug(f"Deleted memory {mem_id}")
            except Exception as e:
                logger.error(f"Error deleting memory: {e}")
        else:
            self._mock_storage = [m for m in self._mock_storage if m["id"] != mem_id]
    
    def __len__(self) -> int:
        """Number of memories."""
        if CHROMADB_AVAILABLE and self.collection:
            return self.collection.count()
        return len(self._mock_storage)
    
    def __repr__(self) -> str:
        return (
            f"KnowledgeRAG(memories={len(self)}, "
            f"backend={'chromadb' if CHROMADB_AVAILABLE else 'mock'}, "
            f"embedding={self.embedding_model})"
        )
    
        return (
            f"KnowledgeRAG(memories={len(self)}, "
            f"backend={'chromadb' if CHROMADB_AVAILABLE else 'mock'}, "
            f"embedding={self.embedding_model})"
        )


# ============================================================================
# Document Loading Utilities
# ============================================================================

def load_documents_from_file(
    file_path: str,
    chunk_by: Literal["function", "paragraph", "fixed"] = "function",
    chunk_size: int = 500,
    knowledge_type: KnowledgeType = "semantic"
) -> List[tuple[str, MemoryMetadata]]:
    """
    Load and chunk documents from file.
    
    Args:
        file_path: Path to document file
        chunk_by: Chunking strategy (function/paragraph/fixed)
        chunk_size: Size for fixed chunking
        knowledge_type: Knowledge type for all chunks
    
    Returns:
        List of (content, metadata) tuples ready for add_memories_bulk
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return []
    
    if chunk_by == "function":
        chunks = _chunk_by_function(content)
    elif chunk_by == "paragraph":
        chunks = _chunk_by_paragraph(content)
    else:  # fixed
        chunks = _chunk_fixed(content, chunk_size)
    
    # Create metadata for each chunk
    source = Path(file_path).name
    memories = []
    for chunk in chunks:
        if len(chunk.strip()) < 20:  # Skip only very tiny chunks (was 50, too aggressive)
            continue
        metadata = MemoryMetadata(
            knowledge_type=knowledge_type,
            memory_tier="long_term",  # Loaded docs are LTM by default
            source=source,
            confidence_score=0.8  # Default confidence for loaded docs
        )
        memories.append((chunk, metadata))
    
    logger.info(f"Loaded {len(memories)} chunks from {file_path}")
    return memories


def _chunk_by_function(content: str) -> List[str]:
    """
    Chunk by function/class definitions (Python-aware).
    
    Extracts each function and class as a separate chunk.
    """
    import re
    
    chunks = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Found a function or class definition
        if stripped.startswith('def ') or stripped.startswith('class '):
            # Start collecting this function/class
            func_lines = [line]
            base_indent = len(line) - len(line.lstrip())
            i += 1
            
            # Collect all indented lines that belong to this function
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                # Empty lines are part of the function
                if not next_stripped:
                    func_lines.append(next_line)
                    i += 1
                    continue
                
                # Check indent
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If indented more than base, it's part of the function
                if next_indent > base_indent:
                    func_lines.append(next_line)
                    i += 1
                # If at same level and it's another def/class, stop here
                elif next_indent == base_indent and (next_stripped.startswith('def ') or next_stripped.startswith('class ')):
                    break
                # If dedented, stop
                elif next_indent < base_indent:
                    break
                else:
                    # Same indent but not def/class - might be after function
                    break
            
            # Save this function/class
            chunk_text = '\n'.join(func_lines)
            chunks.append(chunk_text)
        else:
            i += 1
    
    return chunks


def _chunk_by_paragraph(content: str) -> List[str]:
    """Chunk by paragraphs (double newline separator)."""
    chunks = content.split('\n\n')
    return [c.strip() for c in chunks if len(c.strip()) > 50]


def _chunk_fixed(content: str, size: int) -> List[str]:
    """Chunk by fixed character size with overlap."""
    chunks = []
    overlap = size // 4  # 25% overlap
    start = 0
    
    while start < len(content):
        end = start + size
        chunk = content[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    
    return chunks


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Example 1: Basic usage with hierarchical memory
    print("=== Example 1: Basic RAG with hierarchical memory ===")
    rag = KnowledgeRAG(persist_dir="./data/chroma_db_demo")
    
    # Add short-term memory (user interaction)
    rag.add_memory(
        "User prefers Python over JavaScript for backend development",
        metadata=MemoryMetadata(
            knowledge_type="episodic",
            memory_tier="short_term",
            source="user_conversation",
            tags=["preferences", "languages"]
        )
    )
    
    # Add long-term memory (system knowledge)
    rag.add_memory(
        "FastAPI is a modern Python web framework with async support and automatic OpenAPI docs",
        metadata=MemoryMetadata(
            knowledge_type="semantic",
            memory_tier="long_term",
            source="documentation",
            confidence_score=0.95,
            tags=["fastapi", "python", "web"]
        )
    )
    
    # Retrieve with semantic search
    results = rag.retrieve("What web framework should I use for Python?", top_k=2)
    print(f"\nRetrieved {len(results)} results:")
    for i, res in enumerate(results, 1):
        print(f"\n{i}. Score: {res.score:.3f}, Tier: {res.metadata.memory_tier}")
        print(f"   Content: {res.content[:100]}...")
    
    # Get stats
    stats = rag.get_stats()
    print(f"\nRAG Stats: {stats}")
    
    # Consolidate memories
    consolidation = rag.consolidate_memories()
    print(f"\nConsolidation: {consolidation}")
    
    # Example 2: Bulk loading from documents
    print("\n=== Example 2: Bulk document loading ===")
    # Load from codebase file
    doc_memories = load_documents_from_file(
        "./src/hlcs/orchestrator.py",
        chunk_by="function",
        knowledge_type="procedural"
    )
    
    if doc_memories:
        contents = [m[0] for m in doc_memories]
        metadatas = [m[1] for m in doc_memories]
        ids = rag.add_memories_bulk(contents, metadatas)
        print(f"Loaded {len(ids)} code chunks from orchestrator.py")
    
    # Example 3: Metadata filtering
    print("\n=== Example 3: Metadata filtering ===")
    episodic_memories = rag.search_by_metadata(
        knowledge_type="episodic",
        memory_tier="short_term"
    )
    print(f"Found {len(episodic_memories)} episodic short-term memories")
    
    # Cleanup
    print("\n=== Cleanup ===")
    print(f"Final memory count: {len(rag)}")
    print(f"RAG: {rag}")

