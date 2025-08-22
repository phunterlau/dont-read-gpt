import sqlite3
import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "discord_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    summary TEXT,
                    file_path TEXT,
                    content_preview TEXT,
                    user_id TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            ''')
            
            # Add new columns if they don't exist (for migration)
            try:
                cursor.execute('ALTER TABLE documents ADD COLUMN user_id TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE documents ADD COLUMN created_at DATETIME')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE documents ADD COLUMN updated_at DATETIME')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create keywords table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
                    UNIQUE(document_id, keyword)
                )
            ''')
            
            # Create embeddings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    embedding_vector TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            ''')
            
            # Create user_profiles table for personalized memory
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    current_memory_profile TEXT NOT NULL,
                    raw_memories TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_url ON documents(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_timestamp ON documents(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_document_id ON keywords(document_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id)')
            
            conn.commit()
    
    def check_existing_document(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if a document already exists and return its info if found."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, url, type, timestamp, summary, user_id, updated_at
                FROM documents
                WHERE url = ?
            ''', (url,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def is_document_outdated(self, timestamp: float, days_threshold: int = 7) -> bool:
        """Check if a document is older than the specified threshold in days."""
        current_time = time.time()
        threshold_seconds = days_threshold * 24 * 60 * 60  # Convert days to seconds
        return (current_time - timestamp) > threshold_seconds
    
    def add_document(self, url: str, doc_type: str, timestamp: float, summary: str, 
                    file_path: str, keywords: List[str], embedding: List[float], 
                    content_preview: str = None, user_id: str = None) -> int:
        """Add a new document or update existing one and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            current_time = time.time()
            current_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
            
            # Check if document already exists
            cursor.execute('SELECT id, created_at FROM documents WHERE url = ?', (url,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing document
                doc_id, created_at = existing
                cursor.execute('''
                    UPDATE documents 
                    SET type = ?, timestamp = ?, summary = ?, file_path = ?, 
                        content_preview = ?, user_id = ?, updated_at = ?
                    WHERE id = ?
                ''', (doc_type, timestamp, summary, file_path, content_preview, user_id, current_datetime, doc_id))
                document_id = doc_id
            else:
                # Insert new document
                cursor.execute('''
                    INSERT INTO documents 
                    (url, type, timestamp, summary, file_path, content_preview, user_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (url, doc_type, timestamp, summary, file_path, content_preview, user_id, current_datetime, current_datetime))
                document_id = cursor.lastrowid
            
            # Clear existing keywords for this document
            cursor.execute('DELETE FROM keywords WHERE document_id = ?', (document_id,))
            
            # Insert keywords
            for keyword in keywords:
                cursor.execute('''
                    INSERT OR IGNORE INTO keywords (document_id, keyword)
                    VALUES (?, ?)
                ''', (document_id, keyword))
            
            # Clear existing embeddings for this document
            cursor.execute('DELETE FROM embeddings WHERE document_id = ?', (document_id,))
            
            # Insert embedding
            if embedding:
                embedding_json = json.dumps(embedding)
                cursor.execute('''
                    INSERT INTO embeddings (document_id, embedding_vector)
                    VALUES (?, ?)
                ''', (document_id, embedding_json))
            
            conn.commit()
            return document_id
    
    def update_document(self, document_id: int, summary: str, keywords: List[str], 
                       embedding: List[float], content_preview: str = None, 
                       user_id: str = None) -> bool:
        """Update an existing document with new summary, keywords, and embedding."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            current_time = time.time()
            current_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
            
            # Update document
            cursor.execute('''
                UPDATE documents 
                SET summary = ?, content_preview = ?, user_id = ?, updated_at = ?
                WHERE id = ?
            ''', (summary, content_preview, user_id, current_datetime, document_id))
            
            if cursor.rowcount == 0:
                return False  # Document not found
            
            # Clear and re-insert keywords
            cursor.execute('DELETE FROM keywords WHERE document_id = ?', (document_id,))
            for keyword in keywords:
                cursor.execute('''
                    INSERT OR IGNORE INTO keywords (document_id, keyword)
                    VALUES (?, ?)
                ''', (document_id, keyword))
            
            # Clear and re-insert embedding
            cursor.execute('DELETE FROM embeddings WHERE document_id = ?', (document_id,))
            if embedding:
                embedding_json = json.dumps(embedding)
                cursor.execute('''
                    INSERT INTO embeddings (document_id, embedding_vector)
                    VALUES (?, ?)
                ''', (document_id, embedding_json))
            
            conn.commit()
            return True
    
    def get_document_by_id(self, document_id: int, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get a document by its ID, optionally filtered by user_id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT * FROM documents WHERE id = ? AND user_id = ?
                ''', (document_id, user_id))
            else:
                cursor.execute('''
                    SELECT * FROM documents WHERE id = ?
                ''', (document_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            document = dict(row)
            
            # Get keywords
            cursor.execute('''
                SELECT keyword FROM keywords WHERE document_id = ?
            ''', (document_id,))
            document['keywords'] = [row[0] for row in cursor.fetchall()]
            
            # Get embedding
            cursor.execute('''
                SELECT embedding_vector FROM embeddings WHERE document_id = ?
            ''', (document_id,))
            embedding_row = cursor.fetchone()
            if embedding_row:
                document['embeddings'] = json.loads(embedding_row[0])
            else:
                document['embeddings'] = []
            
            return document
    
    def search_by_url(self, pattern: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Search documents by URL pattern, optionally filtered by user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT id, url, type, timestamp, summary, user_id, updated_at
                    FROM documents
                    WHERE url LIKE ? AND user_id = ?
                    ORDER BY updated_at DESC
                ''', (f'%{pattern}%', user_id))
            else:
                cursor.execute('''
                    SELECT id, url, type, timestamp, summary, user_id, updated_at
                    FROM documents
                    WHERE url LIKE ?
                    ORDER BY updated_at DESC
                ''', (f'%{pattern}%',))
            
            return [dict(row) for row in cursor.fetchall()]

    def search_by_keyword(self, keyword: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Search documents by keyword, optionally filtered by user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT DISTINCT d.id, d.url, d.type, d.timestamp, d.summary, d.user_id, d.updated_at
                    FROM documents d
                    JOIN keywords k ON d.id = k.document_id
                    WHERE k.keyword LIKE ? AND d.user_id = ?
                    ORDER BY d.updated_at DESC
                ''', (f'%{keyword}%', user_id))
            else:
                cursor.execute('''
                    SELECT DISTINCT d.id, d.url, d.type, d.timestamp, d.summary, d.user_id, d.updated_at
                    FROM documents d
                    JOIN keywords k ON d.id = k.document_id
                    WHERE k.keyword LIKE ?
                    ORDER BY d.updated_at DESC
                ''', (f'%{keyword}%',))
            
            results = []
            for row in cursor.fetchall():
                doc = dict(row)
                
                # Get keywords for this document
                cursor.execute('''
                    SELECT keyword FROM keywords WHERE document_id = ?
                ''', (doc['id'],))
                doc['keywords'] = [k[0] for k in cursor.fetchall()]
                
                results.append(doc)
            
            return results
    
    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, url, type, timestamp, summary, user_id, updated_at
                FROM documents
                WHERE user_id = ?
                ORDER BY updated_at DESC
            ''', (user_id,))
            
            results = []
            for row in cursor.fetchall():
                doc = dict(row)
                
                # Get keywords for this document
                cursor.execute('''
                    SELECT keyword FROM keywords WHERE document_id = ?
                ''', (doc['id'],))
                doc['keywords'] = [k[0] for k in cursor.fetchall()]
                
                results.append(doc)
            
            return results
    
    def get_documents_by_type(self, doc_type: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all documents of a specific type, optionally filtered by user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT id, url, type, timestamp, summary, user_id, updated_at
                    FROM documents
                    WHERE type = ? AND user_id = ?
                    ORDER BY updated_at DESC
                ''', (doc_type, user_id))
            else:
                cursor.execute('''
                    SELECT id, url, type, timestamp, summary, user_id, updated_at
                    FROM documents
                    WHERE type = ?
                    ORDER BY updated_at DESC
                ''', (doc_type,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get database statistics, optionally filtered by user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            user_filter = "WHERE user_id = ?" if user_id else ""
            user_params = (user_id,) if user_id else ()
            
            # Total documents
            cursor.execute(f'SELECT COUNT(*) FROM documents {user_filter}', user_params)
            total_documents = cursor.fetchone()[0]
            
            # Documents by type
            cursor.execute(f'''
                SELECT type, COUNT(*) 
                FROM documents 
                {user_filter}
                GROUP BY type
            ''', user_params)
            documents_by_type = dict(cursor.fetchall())
            
            # Total keywords (for user's documents)
            if user_id:
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM keywords k
                    JOIN documents d ON k.document_id = d.id
                    WHERE d.user_id = ?
                ''', (user_id,))
            else:
                cursor.execute('SELECT COUNT(*) FROM keywords')
            total_keywords = cursor.fetchone()[0]
            
            # Unique keywords (for user's documents)
            if user_id:
                cursor.execute('''
                    SELECT COUNT(DISTINCT keyword) 
                    FROM keywords k
                    JOIN documents d ON k.document_id = d.id
                    WHERE d.user_id = ?
                ''', (user_id,))
            else:
                cursor.execute('SELECT COUNT(DISTINCT keyword) FROM keywords')
            unique_keywords = cursor.fetchone()[0]
            
            # Top keywords (for user's documents)
            if user_id:
                cursor.execute('''
                    SELECT k.keyword, COUNT(*) as count
                    FROM keywords k
                    JOIN documents d ON k.document_id = d.id
                    WHERE d.user_id = ?
                    GROUP BY k.keyword
                    ORDER BY count DESC
                    LIMIT 10
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT keyword, COUNT(*) as count
                    FROM keywords
                    GROUP BY keyword
                    ORDER BY count DESC
                    LIMIT 10
                ''')
            top_keywords = dict(cursor.fetchall())
            
            # Recent documents
            cursor.execute(f'''
                SELECT id, url, timestamp
                FROM documents
                {user_filter}
                ORDER BY timestamp DESC
                LIMIT 5
            ''', user_params)
            recent_documents = [{'id': row[0], 'url': row[1], 'timestamp': row[2]} 
                              for row in cursor.fetchall()]
            
            return {
                'total_documents': total_documents,
                'documents_by_type': documents_by_type,
                'total_keywords': total_keywords,
                'unique_keywords': unique_keywords,
                'top_keywords': top_keywords,
                'recent_documents': recent_documents
            }
    
    def get_related_documents(self, document_id: int, limit: int = 5, user_id: str = None) -> List[Dict[str, Any]]:
        """Get documents related to the given document based on shared keywords, optionally filtered by user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            user_filter = "AND d.user_id = ?" if user_id else ""
            user_params = (document_id, document_id, user_id, limit) if user_id else (document_id, document_id, limit)
            
            cursor.execute(f'''
                SELECT DISTINCT d.id, d.url, d.type, d.timestamp, d.summary,
                       COUNT(k2.keyword) as shared_keywords
                FROM documents d
                JOIN keywords k1 ON d.id = k1.document_id
                JOIN keywords k2 ON k1.keyword = k2.keyword
                WHERE k2.document_id = ? AND d.id != ? {user_filter}
                GROUP BY d.id, d.url, d.type, d.timestamp, d.summary
                ORDER BY shared_keywords DESC, d.timestamp DESC
                LIMIT ?
            ''', user_params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def set_user_memory(self, user_id: str, memory_profile: str, raw_memory: str) -> bool:
        """Creates or updates a user's memory profile."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            current_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            
            # Check if user profile already exists
            cursor.execute('SELECT user_id, raw_memories FROM user_profiles WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing profile - append new raw memory to the list
                existing_raw_memories = existing[1] if existing[1] else "[]"
                try:
                    raw_memories_list = json.loads(existing_raw_memories)
                except (json.JSONDecodeError, TypeError):
                    raw_memories_list = []
                
                # Add new raw memory with timestamp
                raw_memories_list.append({
                    "memory": raw_memory,
                    "timestamp": current_datetime
                })
                
                # Keep only the last 10 raw memories to prevent excessive growth
                if len(raw_memories_list) > 10:
                    raw_memories_list = raw_memories_list[-10:]
                
                updated_raw_memories = json.dumps(raw_memories_list)
                
                cursor.execute('''
                    UPDATE user_profiles 
                    SET current_memory_profile = ?, raw_memories = ?, updated_at = ?
                    WHERE user_id = ?
                ''', (memory_profile, updated_raw_memories, current_datetime, user_id))
            else:
                # Insert new profile
                initial_raw_memories = json.dumps([{
                    "memory": raw_memory,
                    "timestamp": current_datetime
                }])
                
                cursor.execute('''
                    INSERT INTO user_profiles 
                    (user_id, current_memory_profile, raw_memories, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, memory_profile, initial_raw_memories, current_datetime, current_datetime))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_memory(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user's memory profile."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, current_memory_profile, raw_memories, created_at, updated_at
                FROM user_profiles
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                profile = dict(row)
                # Parse raw memories JSON
                try:
                    profile['raw_memories'] = json.loads(profile['raw_memories']) if profile['raw_memories'] else []
                except (json.JSONDecodeError, TypeError):
                    profile['raw_memories'] = []
                return profile
            return None
    
    def clear_user_memory(self, user_id: str) -> bool:
        """Clears a user's memory profile."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_recent_documents(self, limit: int = 10, user_id: str = None) -> List[Dict[str, Any]]:
        """Get recent documents, optionally filtered by user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT id, url, type, timestamp, summary, user_id, updated_at
                    FROM documents
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT id, url, type, timestamp, summary, user_id, updated_at
                    FROM documents
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def migrate_from_csv(self, csv_path: str, saved_text_dir: str):
        """Migrate data from the old CSV index system."""
        if not os.path.exists(csv_path):
            return
        
        with open(csv_path, 'r') as f:
            for line in f:
                try:
                    parts = line.strip().split(',')
                    if len(parts) != 3:
                        continue
                    
                    file_type, timestamp, file_path = parts
                    
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as json_file:
                            data = json.load(json_file)
                            
                            # Extract content preview (first 500 chars)
                            content_preview = ""
                            if isinstance(data.get('content'), str):
                                content_preview = data['content'][:500]
                            elif isinstance(data.get('summary'), str):
                                content_preview = data['summary'][:500]
                            
                            self.add_document(
                                url=data.get('url', ''),
                                doc_type=data.get('type', file_type),
                                timestamp=float(data.get('timestamp', timestamp)),
                                summary=data.get('summary', ''),
                                file_path=file_path,
                                keywords=data.get('keywords', []),
                                embedding=data.get('embeddings', []),
                                content_preview=content_preview,
                                user_id=None  # No user ID available from old data
                            )
                            
                except Exception as e:
                    print(f"Error migrating {line}: {e}")
    
    def close(self):
        """Close database connection (placeholder for future connection pooling)."""
        pass
