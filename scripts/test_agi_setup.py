#!/usr/bin/env python3
"""
Quick test del sistema AGI

Verifica que todo esté correctamente instalado y configurado.
"""

import sys
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test 1: Imports básicos."""
    print("\n1️⃣  Testing imports...")
    
    try:
        from hlcs.memory.episodic_memory import MemoryBuffer
        print("   ✅ MemoryBuffer imported")
    except ImportError as e:
        print(f"   ❌ MemoryBuffer import failed: {e}")
        return False
    
    try:
        from hlcs.memory.rag import KnowledgeRAG
        print("   ✅ KnowledgeRAG imported")
    except ImportError as e:
        print(f"   ❌ KnowledgeRAG import failed: {e}")
        return False
    
    try:
        from hlcs.planning.agentes import CodeAgent
        print("   ✅ CodeAgent imported")
    except ImportError as e:
        print(f"   ❌ CodeAgent import failed: {e}")
        return False
    
    try:
        from hlcs.agi_system import Phi4MiniAGI
        print("   ✅ Phi4MiniAGI imported")
    except ImportError as e:
        print(f"   ❌ Phi4MiniAGI import failed: {e}")
        return False
    
    return True


def test_dependencies():
    """Test 2: Dependencias externas."""
    print("\n2️⃣  Testing dependencies...")
    
    # llama-cpp-python
    try:
        from llama_cpp import Llama
        print("   ✅ llama-cpp-python installed")
    except ImportError:
        print("   ⚠️  llama-cpp-python NOT installed (AGI will run in mock mode)")
        print("      Install: pip install llama-cpp-python")
    
    # sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        print("   ✅ sentence-transformers installed")
    except ImportError:
        print("   ⚠️  sentence-transformers NOT installed (RAG disabled)")
        print("      Install: pip install sentence-transformers")
    
    # numpy
    try:
        import numpy
        print("   ✅ numpy installed")
    except ImportError:
        print("   ❌ numpy NOT installed")
        print("      Install: pip install numpy")
        return False
    
    return True


def test_directories():
    """Test 3: Directorios requeridos."""
    print("\n3️⃣  Testing directories...")
    
    dirs = [
        "./models",
        "./data",
        "./data/memory"
    ]
    
    all_exist = True
    for dir_path in dirs:
        p = Path(dir_path)
        if p.exists():
            print(f"   ✅ {dir_path} exists")
        else:
            print(f"   ⚠️  {dir_path} NOT found (will be created if needed)")
            all_exist = False
    
    return True  # No bloqueante


def test_model():
    """Test 4: Modelo Phi-4-mini."""
    print("\n4️⃣  Testing model...")
    
    model_paths = [
        "./models/phi4_mini_q4.gguf",
        "./models/phi-4-mini-q4.gguf",
    ]
    
    for model_path in model_paths:
        p = Path(model_path)
        if p.exists():
            size_mb = p.stat().st_size / (1024 * 1024)
            print(f"   ✅ Model found: {model_path} ({size_mb:.1f} MB)")
            return True
    
    print("   ⚠️  Phi-4-mini model NOT found")
    print("      Download:")
    print("      wget https://huggingface.co/microsoft/phi-4/resolve/main/phi-4-mini-q4.gguf -O models/phi4_mini_q4.gguf")
    
    return False  # No bloqueante para test


def test_memory():
    """Test 5: Memoria episódica."""
    print("\n5️⃣  Testing memory...")
    
    try:
        from hlcs.memory.episodic_memory import MemoryBuffer
        
        # Crear buffer temporal
        memory = MemoryBuffer(
            max_size=10,
            persist_path="./test_memory.json",
            auto_save=False
        )
        
        # Agregar episodio
        memory.add(
            query="Test query",
            answer="Test answer",
            session_id="test_session",
            user_id="test_user"
        )
        
        # Verificar
        assert len(memory) == 1
        recent = memory.get_recent(1)
        assert recent[0].query == "Test query"
        
        # Cleanup
        Path("./test_memory.json").unlink(missing_ok=True)
        
        print("   ✅ MemoryBuffer working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ MemoryBuffer test failed: {e}")
        return False


def test_orchestrator_integration():
    """Test 6: Integración con orchestrator."""
    print("\n6️⃣  Testing orchestrator integration...")
    
    try:
        from hlcs.orchestrator import HLCSOrchestrator
        print("   ✅ Orchestrator imports AGI system successfully")
        return True
    except ImportError as e:
        print(f"   ❌ Orchestrator integration failed: {e}")
        return False


def main():
    print("=" * 60)
    print("HLCS AGI System - Quick Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Directories", test_directories()))
    results.append(("Model", test_model()))
    results.append(("Memory", test_memory()))
    results.append(("Integration", test_orchestrator_integration()))
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:20s}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nYou're ready to use the AGI system!")
        print("\nNext steps:")
        print("  1. Download Phi-4-mini model (if not done)")
        print("  2. Configure config/hlcs.yaml")
        print("  3. Run: python examples/agi_complete_demo.py")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nPlease fix the issues above before using the AGI system.")
        print("\nSee docs/AGI_SETUP.md for detailed setup instructions.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
