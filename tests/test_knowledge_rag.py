"""
Tests for KnowledgeRAG v2.0 with ChromaDB and Hierarchical Memory

Test Coverage:
- ChromaDB persistence and retrieval
- Metadata filtering and semantic search
- Memory hierarchy (STM/LTM)
- Consolidation and auto-promotion
- Document loading utilities
- LangChain integration

Version: 2.0.0
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.memory.rag import (
    KnowledgeRAG,
    MemoryMetadata,
    RetrievalResult,
    load_documents_from_file,
    CHROMADB_AVAILABLE,
    EMBEDDINGS_AVAILABLE
)


@pytest.fixture
def temp_persist_dir():
    """Create temporary directory for ChromaDB."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def rag_instance(temp_persist_dir):
    """Create RAG instance with temporary storage."""
    rag = KnowledgeRAG(
        persist_dir=temp_persist_dir,
        collection_name="test_collection",
        stm_ttl_hours=1,  # Short TTL for testing
        ltm_promotion_threshold=2  # Low threshold for testing
    )
    return rag


class TestMemoryMetadata:
    """Test MemoryMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test creating metadata with defaults."""
        metadata = MemoryMetadata(
            knowledge_type="episodic",
            memory_tier="short_term"
        )
        
        assert metadata.knowledge_type == "episodic"
        assert metadata.memory_tier == "short_term"
        assert metadata.source == "system"
        assert metadata.confidence_score == 1.0
        assert metadata.access_count == 0
        assert metadata.tags == []
    
    def test_metadata_to_dict(self):
        """Test metadata serialization."""
        metadata = MemoryMetadata(
            knowledge_type="semantic",
            memory_tier="long_term",
            source="user",
            tags=["python", "fastapi"]
        )
        
        meta_dict = metadata.to_dict()
        assert meta_dict["knowledge_type"] == "semantic"
        assert meta_dict["memory_tier"] == "long_term"
        assert meta_dict["source"] == "user"
        assert "python" in meta_dict["tags"]
    
    def test_metadata_from_dict(self):
        """Test metadata deserialization."""
        meta_dict = {
            "knowledge_type": "procedural",
            "memory_tier": "short_term",
            "timestamp": "2025-11-07T10:00:00",
            "source": "system",
            "confidence_score": 0.95,
            "access_count": 5,
            "tags": '["code", "algorithm"]'
        }
        
        metadata = MemoryMetadata.from_dict(meta_dict)
        assert metadata.knowledge_type == "procedural"
        assert metadata.confidence_score == 0.95
        assert metadata.access_count == 5
        assert len(metadata.tags) == 2


class TestKnowledgeRAGBasic:
    """Test basic RAG functionality."""
    
    def test_initialization(self, rag_instance):
        """Test RAG initialization."""
        assert rag_instance is not None
        assert rag_instance.collection_name == "test_collection"
        assert rag_instance.stm_ttl_hours == 1
        assert rag_instance.ltm_promotion_threshold == 2
    
    def test_add_single_memory(self, rag_instance):
        """Test adding single memory."""
        content = "Python is a high-level programming language"
        metadata = MemoryMetadata(
            knowledge_type="semantic",
            memory_tier="short_term"
        )
        
        mem_id = rag_instance.add_memory(content, metadata)
        assert mem_id.startswith("mem_")
        assert len(rag_instance) >= 1
    
    def test_add_memory_with_custom_id(self, rag_instance):
        """Test adding memory with custom ID."""
        content = "FastAPI is a modern web framework"
        mem_id = rag_instance.add_memory(
            content,
            id="custom_123"
        )
        assert mem_id == "custom_123"
    
    def test_add_bulk_memories(self, rag_instance):
        """Test bulk memory addition."""
        contents = [
            "Python uses dynamic typing",
            "JavaScript runs in browsers",
            "Rust is memory-safe"
        ]
        metadatas = [
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
            for _ in contents
        ]
        
        ids = rag_instance.add_memories_bulk(contents, metadatas)
        assert len(ids) == 3
        assert len(rag_instance) >= 3
    
    def test_empty_content_raises_error(self, rag_instance):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError):
            rag_instance.add_memory("")


class TestRetrieval:
    """Test semantic retrieval and filtering."""
    
    def test_basic_retrieval(self, rag_instance):
        """Test basic semantic retrieval."""
        # Add some memories
        rag_instance.add_memory(
            "Python is great for data science",
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
        )
        rag_instance.add_memory(
            "JavaScript is great for web development",
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
        )
        
        # Retrieve
        results = rag_instance.retrieve("What language for data?", top_k=2)
        
        # Should work in both mock and real mode
        assert len(results) >= 1
        assert all(isinstance(r, RetrievalResult) for r in results)
    
    def test_retrieval_with_knowledge_type_filter(self, rag_instance):
        """Test retrieval with knowledge type filtering."""
        # Add different knowledge types
        rag_instance.add_memory(
            "User prefers dark mode",
            MemoryMetadata(knowledge_type="episodic", memory_tier="short_term")
        )
        rag_instance.add_memory(
            "Functions return values",
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
        )
        
        # Filter by episodic
        results = rag_instance.retrieve(
            "What does user prefer?",
            knowledge_type="episodic"
        )
        
        # In real mode, should only get episodic
        if CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE:
            assert all(r.metadata.knowledge_type == "episodic" for r in results)
    
    def test_retrieval_with_memory_tier_filter(self, rag_instance):
        """Test retrieval with memory tier filtering."""
        rag_instance.add_memory(
            "Recent interaction",
            MemoryMetadata(knowledge_type="episodic", memory_tier="short_term")
        )
        rag_instance.add_memory(
            "Established fact",
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
        )
        
        # Filter by long-term
        results = rag_instance.retrieve(
            "established knowledge",
            memory_tier="long_term"
        )
        
        if CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE:
            assert all(r.metadata.memory_tier == "long_term" for r in results)
    
    def test_retrieval_with_confidence_filter(self, rag_instance):
        """Test retrieval with minimum confidence filter."""
        rag_instance.add_memory(
            "High confidence fact",
            MemoryMetadata(
                knowledge_type="semantic",
                memory_tier="long_term",
                confidence_score=0.95
            )
        )
        rag_instance.add_memory(
            "Low confidence guess",
            MemoryMetadata(
                knowledge_type="semantic",
                memory_tier="long_term",
                confidence_score=0.3
            )
        )
        
        # Require high confidence
        results = rag_instance.retrieve(
            "confident knowledge",
            min_confidence=0.8
        )
        
        if CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE:
            assert all(r.metadata.confidence_score >= 0.8 for r in results)


class TestMemoryHierarchy:
    """Test short-term and long-term memory management."""
    
    def test_stm_ltm_distinction(self, rag_instance):
        """Test that STM and LTM are tracked separately."""
        # Add STM
        rag_instance.add_memory(
            "Short-term memory content",
            MemoryMetadata(knowledge_type="episodic", memory_tier="short_term")
        )
        
        # Add LTM
        rag_instance.add_memory(
            "Long-term memory content",
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
        )
        
        stats = rag_instance.get_stats()
        if CHROMADB_AVAILABLE:
            assert stats["total_memories"] >= 2
            assert "short_term" in stats
            assert "long_term" in stats
    
    def test_stm_promotion_by_access_count(self, rag_instance):
        """Test STM → LTM promotion based on access count."""
        if not (CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE):
            pytest.skip("Requires ChromaDB and embeddings")
        
        # Add STM
        mem_id = rag_instance.add_memory(
            "Important repeated fact",
            MemoryMetadata(knowledge_type="semantic", memory_tier="short_term"),
            id="test_promotion"
        )
        
        # Access it multiple times (threshold is 2)
        for _ in range(3):
            results = rag_instance.retrieve("important fact")
        
        # Check if promoted
        result = rag_instance.collection.get(ids=[mem_id])
        if result["metadatas"]:
            metadata = result["metadatas"][0]
            # Should be promoted after 2 accesses
            assert metadata["memory_tier"] == "long_term" or metadata["access_count"] >= 2
    
    def test_consolidate_memories(self, rag_instance):
        """Test memory consolidation process."""
        if not CHROMADB_AVAILABLE:
            pytest.skip("Requires ChromaDB")
        
        # Add high-access STM
        rag_instance.add_memory(
            "Frequently accessed",
            MemoryMetadata(
                knowledge_type="semantic",
                memory_tier="short_term",
                access_count=5  # Above threshold
            ),
            id="high_access"
        )
        
        # Add old STM (expired)
        old_timestamp = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        rag_instance.add_memory(
            "Old expired memory",
            MemoryMetadata(
                knowledge_type="episodic",
                memory_tier="short_term",
                timestamp=old_timestamp
            ),
            id="expired"
        )
        
        # Run consolidation
        stats = rag_instance.consolidate_memories()
        
        # Should promote high-access and expire old
        assert "promoted" in stats
        assert "expired" in stats


class TestMetadataSearch:
    """Test metadata-only search functionality."""
    
    def test_search_by_knowledge_type(self, rag_instance):
        """Test searching by knowledge type."""
        if not CHROMADB_AVAILABLE:
            pytest.skip("Requires ChromaDB")
        
        # Add different types
        rag_instance.add_memory(
            "User said hello",
            MemoryMetadata(knowledge_type="episodic", memory_tier="short_term")
        )
        rag_instance.add_memory(
            "Python is object-oriented",
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
        )
        
        # Search episodic
        episodic = rag_instance.search_by_metadata(knowledge_type="episodic")
        assert all(r.metadata.knowledge_type == "episodic" for r in episodic)
    
    def test_search_by_source(self, rag_instance):
        """Test searching by source."""
        if not CHROMADB_AVAILABLE:
            pytest.skip("Requires ChromaDB")
        
        rag_instance.add_memory(
            "User input",
            MemoryMetadata(
                knowledge_type="episodic",
                memory_tier="short_term",
                source="user_conversation"
            )
        )
        
        results = rag_instance.search_by_metadata(source="user_conversation")
        assert all(r.metadata.source == "user_conversation" for r in results)


class TestDocumentLoading:
    """Test document loading utilities."""
    
    def test_load_from_nonexistent_file(self):
        """Test loading from file that doesn't exist."""
        memories = load_documents_from_file("nonexistent.txt")
        assert memories == []
    
    def test_chunk_by_function(self, tmp_path):
        """Test function-based chunking."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def function_one():
    return 1

def function_two():
    return 2

class MyClass:
    def method(self):
        pass
""")
        
        memories = load_documents_from_file(
            str(test_file),
            chunk_by="function",
            knowledge_type="procedural"
        )
        
        assert len(memories) > 0
        # Each memory is (content, metadata) tuple
        assert all(isinstance(m, tuple) and len(m) == 2 for m in memories)
        assert all(m[1].knowledge_type == "procedural" for m in memories)
    
    def test_chunk_by_paragraph(self, tmp_path):
        """Test paragraph-based chunking."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""
Paragraph one with enough content to pass the minimum length requirement.

Paragraph two also with sufficient length to be included in results.
""")
        
        memories = load_documents_from_file(
            str(test_file),
            chunk_by="paragraph"
        )
        
        assert len(memories) >= 1


class TestRAGStats:
    """Test statistics and monitoring."""
    
    def test_get_stats(self, rag_instance):
        """Test getting RAG statistics."""
        # Add some memories
        rag_instance.add_memory(
            "Test content",
            MemoryMetadata(knowledge_type="semantic", memory_tier="long_term")
        )
        
        stats = rag_instance.get_stats()
        assert "total_memories" in stats
        assert stats["total_memories"] >= 1
        
        if CHROMADB_AVAILABLE:
            assert "backend" in stats
            assert stats["backend"] == "chromadb"
            assert "persist_dir" in stats
    
    def test_len_operator(self, rag_instance):
        """Test __len__ operator."""
        initial_len = len(rag_instance)
        
        rag_instance.add_memory(
            "New memory",
            MemoryMetadata(knowledge_type="semantic", memory_tier="short_term")
        )
        
        assert len(rag_instance) == initial_len + 1
    
    def test_repr(self, rag_instance):
        """Test __repr__ string."""
        repr_str = repr(rag_instance)
        assert "KnowledgeRAG" in repr_str
        assert "memories=" in repr_str


class TestDeletion:
    """Test memory deletion operations."""
    
    def test_delete_single_memory(self, rag_instance):
        """Test deleting a single memory."""
        mem_id = rag_instance.add_memory(
            "To be deleted",
            id="delete_me"
        )
        
        initial_count = len(rag_instance)
        rag_instance.delete_memory(mem_id)
        
        assert len(rag_instance) == initial_count - 1
    
    def test_clear_all(self, rag_instance):
        """Test clearing all memories."""
        # Add some memories
        for i in range(3):
            rag_instance.add_memory(f"Memory {i}")
        
        rag_instance.clear_all()
        assert len(rag_instance) == 0


@pytest.mark.skipif(
    not (CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE),
    reason="Requires ChromaDB and sentence-transformers"
)
class TestIntegrationWithDependencies:
    """Integration tests requiring all dependencies."""
    
    def test_end_to_end_workflow(self, temp_persist_dir):
        """Test complete RAG workflow."""
        # Initialize
        rag = KnowledgeRAG(persist_dir=temp_persist_dir)
        
        # Add various memories
        rag.add_memory(
            "Python 3.11+ required for modern syntax",
            MemoryMetadata(
                knowledge_type="semantic",
                memory_tier="long_term",
                source="documentation",
                confidence_score=0.95,
                tags=["python", "requirements"]
            )
        )
        
        rag.add_memory(
            "User prefers async/await over threads",
            MemoryMetadata(
                knowledge_type="episodic",
                memory_tier="short_term",
                source="user_conversation",
                tags=["preferences", "async"]
            )
        )
        
        # Retrieve with semantic search
        results = rag.retrieve("What Python version needed?", top_k=2)
        assert len(results) >= 1
        assert any("Python" in r.content for r in results)
        
        # Retrieve with filters
        filtered = rag.retrieve(
            "user preferences",
            knowledge_type="episodic",
            tags=["preferences"]
        )
        assert len(filtered) >= 1
        
        # Check stats
        stats = rag.get_stats()
        assert stats["total_memories"] >= 2
        assert stats["short_term"] >= 1
        assert stats["long_term"] >= 1
        
        # Consolidate
        consolidation = rag.consolidate_memories()
        assert "promoted" in consolidation
        assert "expired" in consolidation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
