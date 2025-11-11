import sqlite3
import logging
import os
from typing import List, Dict, Any, Optional

class MemoryManager:
    """
    Memory manager for storing and retrieving conversation history.
    
    Note: This implementation uses SQLite, which is a file-based database.
    SQLite does NOT use GRANT/permissions like MySQL/PostgreSQL. Instead,
    it relies on file system permissions. Anyone who can access the database
    file can read/write to it (based on OS file permissions).
    
    If you need database-level permissions and user management, consider:
    - Using PostgreSQL or MySQL with connection credentials
    - Implementing a database server adapter
    """
    
    def __init__(self, db_path: str = "data/sql/conversation_memory.db"):
        """
        Initialize MemoryManager.
        
        Args:
            db_path: Path to SQLite database file.
                    Note: SQLite uses file system permissions, not database grants.
                    The database file will be created if it doesn't exist.
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self._ensure_db_directory()
        self.connect()
        self._create_tables()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    def connect(self):
        """
        Establish a database connection.
        
        Note: SQLite doesn't require username/password. Access is controlled
        by file system permissions. To secure the database:
        1. Set proper file permissions (chmod) on the database file
        2. Use file system access controls
        3. For production, consider using PostgreSQL/MySQL with proper grants
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.logger.info(f"Connected to memory database: {self.db_path}")
            self.logger.info("Note: SQLite uses file permissions, not database grants")
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise
    
    def disconnect(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Memory database connection closed")
    
    def _create_tables(self):
        """Create conversations table if it doesn't exist."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_session 
                ON conversations(user_id, session_id, created_at DESC)
            """)
            
            self.connection.commit()
            self.logger.info("Conversations table created/verified")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating tables: {e}")
            raise
    
    def save_memory(self, user_id: str, session_id: str, question: str, answer: str) -> Optional[int]:
        """
        Save a conversation to memory.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            question: User question
            answer: Assistant answer
            
        Returns:
            ID of the inserted record, or None if error
        """
        if not self.connection:
            raise ConnectionError("Database not connected")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO conversations (user_id, session_id, question, answer)
                VALUES (?, ?, ?, ?)
            """, (user_id, session_id, question, answer))
            self.connection.commit()
            memory_id = cursor.lastrowid
            self.logger.info(f"Saved memory for user_id={user_id}, session_id={session_id}")
            return memory_id
        except sqlite3.Error as e:
            self.logger.error(f"Error saving memory: {e}")
            self.connection.rollback()
            raise
    
    def get_memory(self, user_id: str, session_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get top K most recent conversations for a user and session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            top_k: Number of recent conversations to retrieve (default: 5)
            
        Returns:
            List of conversation dictionaries with keys: id, user_id, session_id, 
            question, answer, created_at in chronological order (oldest first)
        """
        if not self.connection:
            raise ConnectionError("Database not connected")
        
        try:
            cursor = self.connection.cursor()
            # Get the most recent conversations but return them in chronological order
            cursor.execute("""
                SELECT id, user_id, session_id, question, answer, created_at
                FROM (
                    SELECT id, user_id, session_id, question, answer, created_at
                    FROM conversations
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ) AS recent_conversations
                ORDER BY created_at ASC
            """, (user_id, session_id, top_k))
            
            rows = cursor.fetchall()
            # Convert to list of dicts in chronological order (oldest first)
            memories = [dict(row) for row in rows]
            self.logger.info(f"Retrieved {len(memories)} memories for user_id={user_id}, session_id={session_id}")
            return memories
        except sqlite3.Error as e:
            self.logger.error(f"Error getting memory: {e}")
            raise
    
    def get_memory_as_conversation(self, user_id: str, session_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get memory as conversation format for AgentWithMCP.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            top_k: Number of recent conversations to retrieve (default: 5)
            
        Returns:
            List of conversation dictionaries with 'role' and 'content' keys
            in chronological order (oldest first)
        """
        memories = self.get_memory(user_id, session_id, top_k)
        conversation = []
        for memory in memories:
            conversation.append({
                "role": "user",
                "content": memory["question"]
            })
            conversation.append({
                "role": "assistant",
                "content": memory["answer"]
            })
        return conversation

