"""
HLCS Package

High-Level Consciousness System - API-first strategic orchestration.
"""

__version__ = "1.0.0"
__all__ = ["HLCSOrchestrator", "SARAiMCPClient"]

# Lazy imports to avoid circular dependencies
def get_orchestrator():
    from .orchestrator import HLCSOrchestrator
    return HLCSOrchestrator

def get_mcp_client():
    from .mcp_client import SARAiMCPClient
    return SARAiMCPClient
