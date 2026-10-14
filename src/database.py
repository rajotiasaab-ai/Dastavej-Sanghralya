"""Database layer with SQLite FTS5 for lightning-fast full-text search.
Operates 100% offline with zero cloud connectivity.
"""

import sqlite3
import re
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from src.parser import ParsedDocx

class Database:
    """Encapsulates SQLite connection and FTS5 operations."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Optimize performance with WAL journal mode and normal synchronous
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def init_db(self) -> None:
        """Create tables and FTS5 virtual index if they don't exist."""
        with self.get_connection() as conn:
            # Metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    title TEXT DEFAULT '',
                    author TEXT DEFAULT '',
                    last_modified_by TEXT DEFAULT '',
                    created_at TEXT DEFAULT '',
                    word_count INTEGER DEFAULT 0,
                    indexed_at REAL NOT NULL,
                    content TEXT DEFAULT ''
                );
            """)

            # Index for fast path & mtime lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_path ON documents(path);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_mtime ON documents(mtime);")

            # FTS5 virtual table for full-text searching
            # Uses content='' (external content) to maintain an efficient index
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    filename,
                    title,
                    author,
                    content,
                    content='documents',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                );
            """)

            # Create sync triggers to keep FTS5 synchronized with documents table
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS docs_ai AFTER INSERT ON documents BEGIN
                    INSERT INTO documents_fts(rowid, filename, title, author, content)
                    VALUES (new.id, new.filename, new.title, new.author, new.content);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS docs_ad AFTER DELETE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, filename, title, author, content)
                    VALUES ('delete', old.id, old.filename, old.title, old.author, old.content);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS docs_au AFTER UPDATE ON documents BEGIN
                    INSERT INTO documents_fts(documents_fts, rowid, filename, title, author, content)
                    VALUES ('delete', old.id, old.filename, old.title, old.author, old.content);
                    INSERT INTO documents_fts(rowid, filename, title, author, content)
                    VALUES (new.id, new.filename, new.title, new.author, new.content);
                END;
            """)

    def get_document_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        norm_path = str(Path(path).resolve())
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, path, filename, file_size, mtime FROM documents WHERE path = ?",
                (norm_path,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def upsert_document(self, doc: ParsedDocx) -> bool:
        """Insert or update a document. Returns True if modified/inserted."""
        norm_path = str(Path(doc.file_path).resolve())
        now = time.time()

        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, file_size, mtime FROM documents WHERE path = ?",
                (norm_path,)
            )
            existing = cursor.fetchone()

            if existing:
                # If size and mtime match, skip re-indexing
                if existing["file_size"] == doc.file_size and abs(existing["mtime"] - doc.modified_time) < 0.001:
                    return False
                
                # Update existing
                conn.execute("""
                    UPDATE documents
                    SET filename = ?, file_size = ?, mtime = ?, title = ?, author = ?,
                        last_modified_by = ?, created_at = ?, word_count = ?,
                        indexed_at = ?, content = ?
                    WHERE id = ?
                """, (
                    doc.file_name, doc.file_size, doc.modified_time, doc.title, doc.author,
                    doc.last_modified_by, doc.created_at, doc.word_count,
                    now, doc.content, existing["id"]
                ))
            else:
                # Insert new
                conn.execute("""
                    INSERT INTO documents (
                        path, filename, file_size, mtime, title, author,
                        last_modified_by, created_at, word_count, indexed_at, content
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    norm_path, doc.file_name, doc.file_size, doc.modified_time,
                    doc.title, doc.author, doc.last_modified_by, doc.created_at,
                    doc.word_count, now, doc.content
                ))
            conn.commit()
            return True

    def remove_document(self, path: str) -> bool:
        norm_path = str(Path(path).resolve())
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE path = ?", (norm_path,))
            conn.commit()
            return cursor.rowcount > 0

    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_all_indexed_paths(self) -> Set[str]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT path FROM documents")
            return {row["path"] for row in cursor.fetchall()}

    def prune_missing_files(self, existing_paths: Set[str]) -> int:
        """Removes records for files that no longer exist."""
        with self.get_connection() as conn:
            all_paths = self.get_all_indexed_paths()
            missing = all_paths - existing_paths
            if not missing:
                return 0
            
            # Delete in chunks to avoid variable limits
            deleted = 0
            missing_list = list(missing)
            chunk_size = 500
            for i in range(0, len(missing_list), chunk_size):
                chunk = missing_list[i:i + chunk_size]
                placeholders = ",".join("?" * len(chunk))
                cursor = conn.execute(f"DELETE FROM documents WHERE path IN ({placeholders})", chunk)
                deleted += cursor.rowcount
            conn.commit()
            return deleted

    @staticmethod
    def _sanitize_fts_query(user_query: str, scope: str = "all") -> str:
        """Sanitizes user input into a safe, flexible SQLite FTS5 query."""
        raw = user_query.strip()
        if not raw:
            return ""

        # Extract quoted exact phrases
        phrases = re.findall(r'"([^"]*)"', raw)
        # Remaining words
        clean_no_phrases = re.sub(r'"[^"]*"', ' ', raw)
        # Extract alphanumeric words
        words = re.findall(r'[\w\.-]+', clean_no_phrases, re.UNICODE)

        sub_queries = []
        for p in phrases:
            p_clean = p.strip()
            if p_clean:
                sub_queries.append(f'"{p_clean}"')

        for w in words:
            # Escape quotes if any
            w_clean = w.replace('"', '')
            if w_clean:
                # Add prefix match for each word so typing "invo" matches "invoice"
                sub_queries.append(f'"{w_clean}"*')

        if not sub_queries:
            return ""

        combined = " AND ".join(sub_queries)

        if scope == "title":
            return f"filename: ({combined}) OR title: ({combined})"
        elif scope == "content":
            return f"content: ({combined})"
        else: # "all"
            return combined

    def search_documents(
        self,
        query_str: str = "",
        scope: str = "all",
        sort_by: str = "rank",
        limit: int = 150,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search documents. If query_str is empty, returns all documents ordered by mtime.
        Returns: (results_list, total_matches_count)
        """
        query_str = query_str.strip()
        
        with self.get_connection() as conn:
            # Case 1: Empty search query -> Return all documents
            if not query_str:
                order_clause = "ORDER BY mtime DESC"
                if sort_by == "name":
                    order_clause = "ORDER BY filename COLLATE NOCASE ASC"
                elif sort_by == "size":
                    order_clause = "ORDER BY file_size DESC"

                count_row = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
                total_cnt = count_row["cnt"] if count_row else 0

                sql = f"""
                    SELECT 
                        id, path, filename, file_size, mtime, title, author,
                        word_count, indexed_at,
                        '' as snippet_text,
                        0.0 as rank
                    FROM documents
                    {order_clause}
                    LIMIT ? OFFSET ?
                """
                cursor = conn.execute(sql, (limit, offset))
                return [dict(row) for row in cursor.fetchall()], total_cnt

            # Case 2: Full-text search with FTS5
            fts_query = self._sanitize_fts_query(query_str, scope)
            if not fts_query:
                return [], 0

            # Determine order
            order_clause = "ORDER BY rank ASC" # BM25: smaller (more negative) is better in FTS5
            if sort_by == "date":
                order_clause = "ORDER BY d.mtime DESC"
            elif sort_by == "name":
                order_clause = "ORDER BY d.filename COLLATE NOCASE ASC"
            elif sort_by == "size":
                order_clause = "ORDER BY d.file_size DESC"

            try:
                # Count total matches
                count_sql = """
                    SELECT COUNT(*) as cnt
                    FROM documents_fts
                    WHERE documents_fts MATCH ?
                """
                count_row = conn.execute(count_sql, (fts_query,)).fetchone()
                total_cnt = count_row["cnt"] if count_row else 0

                # Fetch matches with snippet
                # snippet(documents_fts, column_index, start_marker, end_marker, ellipsis, max_tokens)
                # column_index 3 is 'content'
                sql = f"""
                    SELECT 
                        d.id, d.path, d.filename, d.file_size, d.mtime, d.title, d.author,
                        d.word_count, d.indexed_at,
                        snippet(documents_fts, 3, '«HL»', '«/HL»', '...', 18) as snippet_text,
                        bm25(documents_fts) as rank
                    FROM documents_fts
                    JOIN documents d ON d.id = documents_fts.rowid
                    WHERE documents_fts MATCH ?
                    {order_clause}
                    LIMIT ? OFFSET ?
                """
                cursor = conn.execute(sql, (fts_query, limit, offset))
                results = [dict(row) for row in cursor.fetchall()]
                return results, total_cnt
                
            except sqlite3.OperationalError as e:
                # Fallback to simple LIKE query on filename/title/content if FTS fails
                fallback_term = f"%{query_str}%"
                count_sql = """
                    SELECT COUNT(*) as cnt FROM documents 
                    WHERE filename LIKE ? OR title LIKE ? OR content LIKE ?
                """
                count_row = conn.execute(count_sql, (fallback_term, fallback_term, fallback_term)).fetchone()
                total_cnt = count_row["cnt"] if count_row else 0

                sql = """
                    SELECT 
                        id, path, filename, file_size, mtime, title, author,
                        word_count, indexed_at,
                        '' as snippet_text,
                        0.0 as rank
                    FROM documents
                    WHERE filename LIKE ? OR title LIKE ? OR content LIKE ?
                    ORDER BY mtime DESC
                    LIMIT ? OFFSET ?
                """
                cursor = conn.execute(sql, (fallback_term, fallback_term, fallback_term, limit, offset))
                return [dict(row) for row in cursor.fetchall()], total_cnt

    def get_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT 
                    COUNT(*) as total_docs,
                    COALESCE(SUM(word_count), 0) as total_words,
                    COALESCE(SUM(file_size), 0) as total_size_bytes
                FROM documents
            """).fetchone()
            return dict(row) if row else {"total_docs": 0, "total_words": 0, "total_size_bytes": 0}

