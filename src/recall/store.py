"""Memory storage using SQLite and numpy for vector search."""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import numpy as np

from .embedder import embed_text, embed_texts, cosine_similarities


@dataclass
class Memory:
    """A single memory entry."""
    id: int
    content: str
    tags: List[str]
    created_at: datetime
    embedding: Optional[np.ndarray] = None
    score: float = 0.0


class MemoryStore:
    """SQLite-backed memory store with semantic search."""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".recall" / "recall.db"
        
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_memories_created 
            ON memories(created_at DESC);
        """)
        self.conn.commit()
    
    def add(self, content: str, tags: Optional[List[str]] = None) -> Memory:
        """Add a new memory."""
        tags = tags or []
        embedding = embed_text(content)
        
        cursor = self.conn.execute(
            "INSERT INTO memories (content, tags, embedding) VALUES (?, ?, ?)",
            (content, json.dumps(tags), embedding.tobytes())
        )
        self.conn.commit()
        
        return Memory(
            id=cursor.lastrowid,
            content=content,
            tags=tags,
            created_at=datetime.now(),
            embedding=embedding
        )
    
    def add_batch(self, items: List[tuple]) -> int:
        """Add multiple memories. Each item is (content, tags)."""
        contents = [item[0] for item in items]
        embeddings = embed_texts(contents)
        
        rows = []
        for i, (content, tags) in enumerate(items):
            rows.append((content, json.dumps(tags or []), embeddings[i].tobytes()))
        
        self.conn.executemany(
            "INSERT INTO memories (content, tags, embedding) VALUES (?, ?, ?)",
            rows
        )
        self.conn.commit()
        return len(rows)
    
    def search(
        self, 
        query: str, 
        limit: int = 10, 
        tags: Optional[List[str]] = None,
        min_score: float = 0.0
    ) -> List[Memory]:
        """Search memories semantically."""
        query_embedding = embed_text(query)
        
        # Fetch all memories (for MVP; could optimize with approximate search later)
        cursor = self.conn.execute(
            "SELECT id, content, tags, embedding, created_at FROM memories"
        )
        rows = cursor.fetchall()
        
        if not rows:
            return []
        
        # Build arrays
        memories = []
        embeddings = []
        
        for row in rows:
            mem_tags = json.loads(row[2])
            
            # Filter by tags if specified
            if tags and not any(t in mem_tags for t in tags):
                continue
            
            memories.append(Memory(
                id=row[0],
                content=row[1],
                tags=mem_tags,
                created_at=datetime.fromisoformat(row[4]),
                embedding=np.frombuffer(row[3], dtype=np.float32)
            ))
            embeddings.append(np.frombuffer(row[3], dtype=np.float32))
        
        if not memories:
            return []
        
        # Compute similarities
        embeddings_array = np.vstack(embeddings)
        scores = cosine_similarities(query_embedding, embeddings_array)
        
        # Attach scores and sort
        for i, mem in enumerate(memories):
            mem.score = float(scores[i])
        
        memories = [m for m in memories if m.score >= min_score]
        memories.sort(key=lambda m: m.score, reverse=True)
        
        return memories[:limit]
    
    def list(
        self, 
        limit: int = 20, 
        tags: Optional[List[str]] = None
    ) -> List[Memory]:
        """List recent memories."""
        cursor = self.conn.execute(
            "SELECT id, content, tags, created_at FROM memories ORDER BY created_at DESC"
        )
        
        memories = []
        for row in cursor:
            mem_tags = json.loads(row[2])
            
            if tags and not any(t in mem_tags for t in tags):
                continue
            
            memories.append(Memory(
                id=row[0],
                content=row[1],
                tags=mem_tags,
                created_at=datetime.fromisoformat(row[3])
            ))
            
            if len(memories) >= limit:
                break
        
        return memories
    
    def delete(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        cursor = self.conn.execute(
            "DELETE FROM memories WHERE id = ?", (memory_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def count(self) -> int:
        """Count total memories."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM memories")
        return cursor.fetchone()[0]
    
    def export_json(self) -> List[dict]:
        """Export all memories as JSON-serializable dicts."""
        cursor = self.conn.execute(
            "SELECT id, content, tags, created_at FROM memories ORDER BY created_at"
        )
        return [
            {
                "id": row[0],
                "content": row[1],
                "tags": json.loads(row[2]),
                "created_at": row[3]
            }
            for row in cursor
        ]
    
    def import_json(self, data: List[dict]) -> int:
        """Import memories from JSON."""
        items = [(d["content"], d.get("tags", [])) for d in data]
        return self.add_batch(items)
    
    def close(self):
        """Close database connection."""
        self.conn.close()
