"""
Episodic Memory Buffer para HLCS AGI

Memoria circular con persistencia en disco. Almacena interacciones
query → answer con contexto temporal y embeddings para retrieval.

Características:
- Buffer circular (FIFO cuando se llena)
- Persistencia JSON en disco
- Embeddings para búsqueda semántica
- Estadísticas de uso

Version: 1.0.0
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Episode:
    """Un episodio en la memoria episódica."""
    query: str
    answer: str
    timestamp: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None  # Para retrieval semántico
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Generar hash único para el episodio
        content = f"{self.query}{self.answer}{self.timestamp}"
        self.metadata["episode_id"] = hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a dict (sin embeddings para ahorrar espacio en disco)."""
        data = asdict(self)
        # No guardar embeddings en disco (se pueden regenerar)
        data.pop("embedding", None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Episode":
        """Crear desde dict."""
        return cls(**data)


class MemoryBuffer:
    """
    Buffer circular de memoria episódica.
    
    Almacena las últimas N interacciones y persiste en disco.
    Permite búsqueda por similaridad semántica si se proveen embeddings.
    
    Example:
        >>> memory = MemoryBuffer(max_size=1000, persist_path="data/memory.json")
        >>> memory.add("¿Qué es AGI?", "AGI es inteligencia artificial general...")
        >>> recent = memory.get_recent(5)
        >>> similar = memory.search_similar("AGI", top_k=3)
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        persist_path: Optional[str] = None,
        auto_save: bool = True,
        enable_embeddings: bool = False
    ):
        """
        Inicializa el buffer de memoria.
        
        Args:
            max_size: Tamaño máximo del buffer (FIFO cuando se llena)
            persist_path: Path para persistir memoria en disco
            auto_save: Guardar automáticamente cada N adds
            enable_embeddings: Calcular embeddings para búsqueda semántica
        """
        self.max_size = max_size
        self.persist_path = Path(persist_path) if persist_path else None
        self.auto_save = auto_save
        self.enable_embeddings = enable_embeddings
        
        self.episodes: List[Episode] = []
        self.stats = {
            "total_episodes": 0,
            "saves": 0,
            "loads": 0
        }
        
        # Cargar memoria existente si hay
        if self.persist_path and self.persist_path.exists():
            self.load()
        
        logger.info(
            f"MemoryBuffer initialized: max_size={max_size}, "
            f"persist={persist_path}, episodes={len(self.episodes)}"
        )
    
    def add(
        self,
        query: str,
        answer: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> Episode:
        """
        Agrega un nuevo episodio a la memoria.
        
        Args:
            query: Query del usuario
            answer: Respuesta generada
            session_id: ID de sesión
            user_id: ID de usuario
            metadata: Metadata adicional
            embedding: Embedding del query (opcional)
        
        Returns:
            Episode creado
        """
        episode = Episode(
            query=query,
            answer=answer,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
            embedding=embedding
        )
        
        # Buffer circular: eliminar más viejo si está lleno
        if len(self.episodes) >= self.max_size:
            removed = self.episodes.pop(0)
            logger.debug(f"Buffer full, removed episode: {removed.metadata.get('episode_id')}")
        
        self.episodes.append(episode)
        self.stats["total_episodes"] += 1
        
        # Auto-guardar cada 10 episodios
        if self.auto_save and self.stats["total_episodes"] % 10 == 0:
            self.save()
        
        logger.debug(f"Added episode: {episode.metadata.get('episode_id')} ({len(self.episodes)}/{self.max_size})")
        
        return episode
    
    def get_recent(self, n: int = 10) -> List[Episode]:
        """
        Obtiene los N episodios más recientes.
        
        Args:
            n: Número de episodios a retornar
        
        Returns:
            Lista de episodios (más reciente primero)
        """
        return list(reversed(self.episodes[-n:]))
    
    def get_by_session(self, session_id: str) -> List[Episode]:
        """
        Obtiene todos los episodios de una sesión.
        
        Args:
            session_id: ID de sesión
        
        Returns:
            Lista de episodios de esa sesión
        """
        return [ep for ep in self.episodes if ep.session_id == session_id]
    
    def get_by_user(self, user_id: str) -> List[Episode]:
        """
        Obtiene todos los episodios de un usuario.
        
        Args:
            user_id: ID de usuario
        
        Returns:
            Lista de episodios de ese usuario
        """
        return [ep for ep in self.episodes if ep.user_id == user_id]
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Episode]:
        """
        Busca episodios similares usando embeddings.
        
        Args:
            query_embedding: Embedding del query a buscar
            top_k: Número de resultados
        
        Returns:
            Lista de episodios similares (ordenados por score)
        """
        if not self.enable_embeddings:
            logger.warning("Embeddings not enabled, returning recent episodes")
            return self.get_recent(top_k)
        
        # Calcular similaridad coseno
        import numpy as np
        
        scored_episodes = []
        for episode in self.episodes:
            if episode.embedding is None:
                continue
            
            # Similaridad coseno
            score = np.dot(query_embedding, episode.embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(episode.embedding)
            )
            scored_episodes.append((episode, score))
        
        # Ordenar por score descendente
        scored_episodes.sort(key=lambda x: x[1], reverse=True)
        
        return [ep for ep, score in scored_episodes[:top_k]]
    
    def clear(self):
        """Limpia toda la memoria (¡CUIDADO!)."""
        self.episodes.clear()
        self.stats["total_episodes"] = 0
        logger.warning("Memory buffer cleared!")
    
    def save(self, path: Optional[Path] = None) -> bool:
        """
        Guarda memoria en disco.
        
        Args:
            path: Path alternativo (usa self.persist_path si None)
        
        Returns:
            True si guardó exitosamente
        """
        save_path = path or self.persist_path
        if not save_path:
            logger.warning("No persist_path configured, skipping save")
            return False
        
        try:
            # Crear directorio si no existe
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Serializar episodios
            data = {
                "episodes": [ep.to_dict() for ep in self.episodes],
                "stats": self.stats,
                "saved_at": datetime.now().isoformat()
            }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.stats["saves"] += 1
            logger.info(f"Memory saved: {len(self.episodes)} episodes → {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return False
    
    def load(self, path: Optional[Path] = None) -> bool:
        """
        Carga memoria desde disco.
        
        Args:
            path: Path alternativo (usa self.persist_path si None)
        
        Returns:
            True si cargó exitosamente
        """
        load_path = path or self.persist_path
        if not load_path or not load_path.exists():
            logger.warning(f"Memory file not found: {load_path}")
            return False
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Deserializar episodios
            self.episodes = [Episode.from_dict(ep) for ep in data.get("episodes", [])]
            loaded_stats = data.get("stats", {})
            self.stats.update(loaded_stats)
            self.stats["loads"] += 1
            
            logger.info(
                f"Memory loaded: {len(self.episodes)} episodes from {load_path} "
                f"(saved at {data.get('saved_at')})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria."""
        return {
            **self.stats,
            "current_episodes": len(self.episodes),
            "max_size": self.max_size,
            "usage_percent": round(len(self.episodes) / self.max_size * 100, 2)
        }
    
    def __len__(self) -> int:
        """Número de episodios en memoria."""
        return len(self.episodes)
    
    def __repr__(self) -> str:
        return f"MemoryBuffer(episodes={len(self.episodes)}/{self.max_size})"


# Funciones de conveniencia
def create_memory_buffer(config: Dict[str, Any]) -> MemoryBuffer:
    """
    Crea un MemoryBuffer desde configuración.
    
    Args:
        config: Dict con configuración (max_size, persist_path, etc.)
    
    Returns:
        MemoryBuffer configurado
    """
    return MemoryBuffer(
        max_size=config.get("max_size", 1000),
        persist_path=config.get("persist_path"),
        auto_save=config.get("auto_save", True),
        enable_embeddings=config.get("enable_embeddings", False)
    )
