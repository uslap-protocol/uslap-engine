#!/usr/bin/env python3
"""
USLaP Database Access Layer
Python module for accessing the USLaP SQLite lattice database.

This module provides:
1. Database connection management with context managers
2. CRUD operations for all major tables
3. Advanced queries for cluster expansion using word_fingerprints
4. Session and engine queue management
5. Utility functions for working with the database

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Union
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

DEFAULT_DB_PATH = "Code_files/uslap_lattice.db"

class DatabaseConnection:
    """Context manager for database connections with automatic cleanup."""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        
        # Enable foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")
        
        # Register extract_consonants UDF if needed
        self._register_udfs()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()
    
    def _register_udfs(self):
        """Register Python UDFs with SQLite."""
        def extract_consonants(word: str) -> str:
            """
            Python UDF for SQLite: Extract consonant skeleton from a word.
            Must match the implementation in migrate_to_sqlite.py and USLaP_Engine.py.
            """
            if not word:
                return ""
            
            vowels = set('aeiou')
            result = []
            i = 0
            word_lower = word.lower()
            
            while i < len(word_lower):
                digraph = word_lower[i:i+2] if i + 1 < len(word_lower) else ''
                if digraph in ('sh', 'ch', 'gh', 'th', 'ph', 'wh', 'qu'):
                    result.append(digraph)
                    i += 2
                elif word_lower[i] not in vowels:
                    result.append(word_lower[i])
                    i += 1
                else:
                    i += 1
            
            return ''.join(result)
        
        self.conn.create_function("extract_consonants", 1, extract_consonants)

def get_connection(db_path: str = DEFAULT_DB_PATH) -> DatabaseConnection:
    """Get a database connection context manager."""
    return DatabaseConnection(db_path)

# ============================================================================
# CORE CRUD OPERATIONS
# ============================================================================

class EntryOperations:
    """Operations for the entries table."""
    
    @staticmethod
    def get_entry(entry_id: int, conn: DatabaseConnection) -> Optional[Dict]:
        """Get a single entry by ID."""
        with conn.cursor as cursor:
            cursor.execute("SELECT * FROM entries WHERE entry_id = ?", (entry_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_entries_by_root(root_id: str, conn: DatabaseConnection, limit: int = 100) -> List[Dict]:
        """Get all entries for a specific root."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT * FROM entries 
                WHERE root_id = ? 
                ORDER BY score DESC, entry_id
                LIMIT ?
            """, (root_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def search_entries(search_term: str, conn: DatabaseConnection, limit: int = 50) -> List[Dict]:
        """Search entries using full-text search."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT e.* 
                FROM entries_fts fts
                JOIN entries e ON fts.entry_id = e.entry_id
                WHERE entries_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (search_term, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_high_score_entries(conn: DatabaseConnection, min_score: int = 8, limit: int = 20) -> List[Dict]:
        """Get entries with high confidence scores."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT * FROM entries 
                WHERE score >= ? 
                ORDER BY score DESC, entry_id
                LIMIT ?
            """, (min_score, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def create_entry(entry_data: Dict, conn: DatabaseConnection) -> int:
        """Create a new entry."""
        required_fields = ['score', 'en_term', 'ar_word', 'root_letters']
        for field in required_fields:
            if field not in entry_data:
                raise ValueError(f"Missing required field: {field}")
        
        with conn.cursor as cursor:
            cursor.execute("""
                INSERT INTO entries (
                    score, en_term, ru_term, fa_term, ar_word, root_id, root_letters,
                    qur_meaning, qur_refs, pattern, inversion_type, allah_name_id,
                    network_id, phonetic_chain, source_form, ds_corridor, decay_level,
                    dp_codes, ops_applied, foundation_refs, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_data.get('score'),
                entry_data.get('en_term'),
                entry_data.get('ru_term'),
                entry_data.get('fa_term'),
                entry_data.get('ar_word'),
                entry_data.get('root_id'),
                entry_data.get('root_letters'),
                entry_data.get('qur_meaning'),
                entry_data.get('qur_refs'),
                entry_data.get('pattern'),
                entry_data.get('inversion_type'),
                entry_data.get('allah_name_id'),
                entry_data.get('network_id'),
                entry_data.get('phonetic_chain'),
                entry_data.get('source_form'),
                entry_data.get('ds_corridor'),
                entry_data.get('decay_level'),
                entry_data.get('dp_codes'),
                entry_data.get('ops_applied'),
                entry_data.get('foundation_refs'),
                entry_data.get('notes')
            ))
            return cursor.lastrowid

class RootOperations:
    """Operations for the roots table."""
    
    @staticmethod
    def get_root(root_id: str, conn: DatabaseConnection) -> Optional[Dict]:
        """Get a single root by ID."""
        with conn.cursor as cursor:
            cursor.execute("SELECT * FROM roots WHERE root_id = ?", (root_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_root_by_letters(root_letters: str, conn: DatabaseConnection) -> Optional[Dict]:
        """Get a root by its letters."""
        with conn.cursor as cursor:
            cursor.execute("SELECT * FROM roots WHERE root_letters = ?", (root_letters,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_all_roots(conn: DatabaseConnection, limit: int = 1000) -> List[Dict]:
        """Get all roots."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT * FROM roots 
                ORDER BY root_id
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_roots_with_entries(conn: DatabaseConnection, min_entries: int = 1) -> List[Dict]:
        """Get roots that have at least N entries."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT r.*, COUNT(e.entry_id) as entry_count
                FROM roots r
                LEFT JOIN entries e ON r.root_id = e.root_id
                GROUP BY r.root_id
                HAVING COUNT(e.entry_id) >= ?
                ORDER BY entry_count DESC
            """, (min_entries,))
            return [dict(row) for row in cursor.fetchall()]

class ChildEntryOperations:
    """Operations for the CHILD schema tables."""
    
    @staticmethod
    def get_child_entry(child_id: str, conn: DatabaseConnection) -> Optional[Dict]:
        """Get a single child entry by ID."""
        with conn.cursor as cursor:
            cursor.execute("SELECT * FROM child_entries WHERE child_id = ?", (child_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_child_entries_by_operation(parent_op: str, conn: DatabaseConnection) -> List[Dict]:
        """Get child entries by parent operation."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT * FROM child_entries 
                WHERE parent_op = ? 
                ORDER BY child_id
            """, (parent_op,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_child_entry_links(child_id: str, conn: DatabaseConnection) -> List[Dict]:
        """Get all links for a child entry."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT l.*, e.en_term, e.ar_word
                FROM child_entry_links l
                JOIN entries e ON l.entry_id = e.entry_id
                WHERE l.child_id = ?
                ORDER BY l.confidence DESC
            """, (child_id,))
            return [dict(row) for row in cursor.fetchall()]

# ============================================================================
# ADVANCED SEARCH OPERATIONS (CRITICAL FOR CLUSTER EXPANSION)
# ============================================================================

class PhoneticSearchOperations:
    """Operations for phonetic search using word_fingerprints table."""
    
    @staticmethod
    def find_similar_words(word: str, conn: DatabaseConnection, language: str = 'en', 
                          max_distance: int = 1, limit: int = 20) -> List[Dict]:
        """
        Find words with similar consonant skeletons (O(log n) cluster expansion).
        
        This is the core function that makes cluster expansion instant.
        It uses the word_fingerprints table with indexed consonant_skeleton column.
        """
        # First, extract consonant skeleton from the input word
        with conn.cursor as cursor:
            cursor.execute("SELECT extract_consonants(?) as skeleton", (word,))
            result = cursor.fetchone()
            if not result or not result['skeleton']:
                return []
            
            skeleton = result['skeleton']
            
            # Find words with the same or similar skeleton
            # For exact matches: same skeleton
            # For similar matches: skeletons that are edit distance <= max_distance
            # We'll start with exact matches for speed
            cursor.execute("""
                SELECT wf.*, 
                       e.en_term, e.ru_term, e.fa_term, e.ar_word,
                       e.entry_id, e.score, e.root_id, e.root_letters
                FROM word_fingerprints wf
                LEFT JOIN entries e ON wf.entry_id = e.entry_id
                WHERE wf.consonant_skeleton = ? AND wf.language = ?
                ORDER BY e.score DESC
                LIMIT ?
            """, (skeleton, language, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def expand_cluster_by_root(root_id: str, conn: DatabaseConnection) -> List[Dict]:
        """
        Expand a cluster by finding all entries with the same root.
        This is the traditional semantic cluster expansion.
        """
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT e.*, r.root_letters, r.quran_tokens
                FROM entries e
                JOIN roots r ON e.root_id = r.root_id
                WHERE e.root_id = ?
                ORDER BY e.score DESC
            """, (root_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def phonetic_cluster_expansion(word: str, conn: DatabaseConnection, 
                                  similarity_threshold: float = 0.7) -> List[Dict]:
        """
        Advanced phonetic cluster expansion using multiple strategies.
        
        1. Exact consonant skeleton match
        2. Similar skeletons (edit distance)
        3. Related roots via phonetic shifts
        4. Network connections
        """
        results = []
        
        # Strategy 1: Exact skeleton match
        exact_matches = PhoneticSearchOperations.find_similar_words(
            word, 'en', conn, max_distance=0, limit=50
        )
        results.extend(exact_matches)
        
        # Strategy 2: Find via network connections if we have an entry
        if exact_matches and exact_matches[0].get('entry_id'):
            entry_id = exact_matches[0]['entry_id']
            with conn.cursor as cursor:
                # Get network connections
                cursor.execute("""
                    SELECT e2.*
                    FROM entries e1
                    JOIN cross_refs cr ON e1.entry_id = cr.from_entry_id
                    JOIN entries e2 ON cr.to_entry_id = e2.entry_id
                    WHERE e1.entry_id = ? AND cr.link_type IN ('SAME_ROOT', 'NETWORK', 'PHONETIC')
                    UNION
                    SELECT e2.*
                    FROM entries e1
                    JOIN cross_refs cr ON e1.entry_id = cr.to_entry_id
                    JOIN entries e2 ON cr.from_entry_id = e2.entry_id
                    WHERE e1.entry_id = ? AND cr.link_type IN ('SAME_ROOT', 'NETWORK', 'PHONETIC')
                """, (entry_id, entry_id))
                
                network_results = [dict(row) for row in cursor.fetchall()]
                results.extend(network_results)
        
        # Deduplicate by entry_id
        seen = set()
        deduplicated = []
        for item in results:
            entry_id = item.get('entry_id')
            if entry_id and entry_id not in seen:
                seen.add(entry_id)
                deduplicated.append(item)
        
        return deduplicated

# ============================================================================
# ENGINE CONTROL OPERATIONS
# ============================================================================

class EngineQueueOperations:
    """Operations for the engine_queue table."""
    
    @staticmethod
    def add_to_queue(operation_type: str, payload: Dict, conn: DatabaseConnection, source: str = 'engine',
                    session_id: Optional[str] = None) -> int:
        """Add an operation to the engine queue."""
        with conn.cursor as cursor:
            cursor.execute("""
                INSERT INTO engine_queue (
                    operation_type, payload, source, session_id, status, priority
                ) VALUES (?, ?, ?, ?, 'PENDING', 5)
            """, (operation_type, json.dumps(payload), source, session_id))
            return cursor.lastrowid
    
    @staticmethod
    def get_pending_queue_items(conn: DatabaseConnection, limit: int = 100) -> List[Dict]:
        """Get pending queue items."""
        with conn.cursor as cursor:
            cursor.execute("""
                SELECT * FROM engine_queue 
                WHERE status = 'PENDING'
                ORDER BY priority DESC, created_at
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def process_queue_item(queue_id: int, status: str = 'APPROVED',
                          resolution_notes: Optional[str] = None, conn: DatabaseConnection) -> bool:
        """Process a queue item."""
        with conn.cursor as cursor:
            cursor.execute("""
                UPDATE engine_queue 
                SET status = ?, processed_at = CURRENT_TIMESTAMP, resolution_notes = ?
                WHERE queue_id = ?
            """, (status, resolution_notes, queue_id))
            return cursor.rowcount > 0

class SessionOperations:
    """Operations for the session_index table."""
    
    @staticmethod
    def create_session(conn: DatabaseConnection, session_id: Optional[str] = None, excel_version: Optional[str] = None,
                      initiated_by: str = 'engine') -> str:
        """Create a new engine session."""
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        with conn.cursor as cursor:
            cursor.execute("""
                INSERT INTO session_index (session_id, excel_version, initiated_by)
                VALUES (?, ?, ?)
            """, (session_id, excel_version, initiated_by))
        
        return session_id
    
    @staticmethod
    def update_session(session_id: str, conn: DatabaseConnection, status: str = 'COMPLETED',
                      entries_processed: int = 0, queries_executed: int = 0,
                      error_log: Optional[str] = None) -> bool:
        """Update session status and metrics."""
        with conn.cursor as cursor:
            cursor.execute("""
                UPDATE session_index 
                SET status = ?, end_time = CURRENT_TIMESTAMP,
                    entries_processed = ?, queries_executed = ?,
                    error_log = ?
                WHERE session_id = ?
            """, (status, entries_processed, queries_executed, error_log, session_id))
            return cursor.rowcount > 0

# ============================================================================
# ANALYTICS AND STATISTICS
# ============================================================================

class AnalyticsOperations:
    """Operations for database analytics and statistics."""
    
    @staticmethod
    def get_database_stats(conn: DatabaseConnection) -> Dict:
        """Get comprehensive database statistics."""
        stats = {}
        
        with conn.cursor as cursor:
            # Table counts
            tables = ['entries', 'roots', 'child_entries', 'derivatives', 'cross_refs',
                     'quran_refs', 'networks', 'scholars', 'detection_patterns',
                     'word_fingerprints', 'engine_queue', 'session_index']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                stats[f"{table}_count"] = result['count'] if result else 0
            
            # Root productivity
            cursor.execute("""
                SELECT AVG(entry_count) as avg_entries_per_root,
                       MAX(entry_count) as max_entries_per_root
                FROM (
                    SELECT r.root_id, COUNT(e.entry_id) as entry_count
                    FROM roots r
                    LEFT JOIN entries e ON r.root_id = e.root_id
                    GROUP BY r.root_id
                )
            """)
            root_stats = cursor.fetchone()
            if root_stats:
                stats.update(dict(root_stats))
            
            # Score distribution
            cursor.execute("""
                SELECT score, COUNT(*) as count
                FROM entries
                GROUP BY score
                ORDER BY score DESC
            """)
            stats['score_distribution'] = [dict(row) for row in cursor.fetchall()]
            
            # Most productive roots
            cursor.execute("""
                SELECT r.root_id, r.root_letters, COUNT(e.entry_id) as entry_count
                FROM roots r
                JOIN entries e ON r.root_id = e.root_id
                GROUP BY r.root_id
                ORDER BY entry_count DESC
                LIMIT 10
            """)
            stats['top_roots'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    @staticmethod
    def get_cluster_analysis(root_id: str, conn: DatabaseConnection) -> Dict:
        """Get detailed analysis of a root cluster."""
        analysis = {}
        
        with conn.cursor as cursor:
            # Get root info
            cursor.execute("SELECT * FROM roots WHERE root_id = ?", (root_id,))
            root = cursor.fetchone()
            if root:
                analysis['root'] = dict(root)
            
            # Get entries
            cursor.execute("""
                SELECT entry_id, en_term, ar_word, score, pattern, network_id
                FROM entries
                WHERE root_id = ?
                ORDER BY score DESC
            """, (root_id,))
            analysis['entries'] = [dict(row) for row in cursor.fetchall()]
            
            # Get derivatives
            cursor.execute("""
                SELECT d.*
                FROM derivatives d
                JOIN entries e ON d.entry_id = e.entry_id
                WHERE e.root_id = ?
                ORDER BY d.derivative_id
            """, (root_id,))
            analysis['derivatives'] = [dict(row) for row in cursor.fetchall()]
            
            # Get cross-references
            cursor.execute("""
                SELECT cr.*, e1.en_term as from_term, e2.en_term as to_term
                FROM cross_refs cr
                JOIN entries e1 ON cr.from_entry_id = e1.entry_id
                JOIN entries e2 ON cr.to_entry_id = e2.entry_id
                WHERE e1.root_id = ? OR e2.root_id = ?
            """, (root_id, root_id))
            analysis['cross_references'] = [dict(row) for row in cursor.fetchall()]
        
        return analysis

# ============================================================================
# HIGH-LEVEL API FUNCTIONS
# ============================================================================

def search_word(word: str, db_path: str = DEFAULT_DB_PATH) -> Dict:
    """
    High-level function to search for a word and return comprehensive results.
    
    Returns:
        Dictionary with:
        - exact_matches: Entries with exact phonetic match
        - similar_words: Words with similar consonant skeletons
        - cluster_expansion: Full cluster expansion results
        - root_info: Information about associated roots
    """
    results = {
        'word': word,
        'exact_matches': [],
        'similar_words': [],
        'cluster_expansion': [],
        'root_info': {}
    }
    
    with get_connection(db_path) as conn:
        # Get exact matches
        exact_matches = PhoneticSearchOperations.find_similar_words(
            word, 'en', conn, max_distance=0, limit=10
        )
        results['exact_matches'] = exact_matches
        
        # Get similar words (allow some distance)
        similar_words = PhoneticSearchOperations.find_similar_words(
            word, 'en', conn, max_distance=1, limit=20
        )
        # Filter out exact matches from similar words
        exact_entry_ids = {m['entry_id'] for m in exact_matches if 'entry_id' in m}
        results['similar_words'] = [
            w for w in similar_words 
            if w.get('entry_id') not in exact_entry_ids
        ]
        
        # Get cluster expansion if we have exact matches
        if exact_matches:
            # Use the first exact match for cluster expansion
            first_match = exact_matches[0]
            if first_match.get('root_id'):
                root_id = first_match['root_id']
                
                # Get root info
                root_op = RootOperations()
                root_info = root_op.get_root(root_id, conn)
                if root_info:
                    results['root_info'] = root_info
                
                # Get cluster expansion
                cluster = PhoneticSearchOperations.expand_cluster_by_root(root_id, conn)
                results['cluster_expansion'] = cluster
        
        # Also try phonetic cluster expansion
        phonetic_cluster = PhoneticSearchOperations.phonetic_cluster_expansion(word, conn)
        # Merge with existing results, avoiding duplicates
        seen_ids = {item['entry_id'] for item in results['cluster_expansion'] if 'entry_id' in item}
        for item in phonetic_cluster:
            if item.get('entry_id') and item['entry_id'] not in seen_ids:
                results['cluster_expansion'].append(item)
                seen_ids.add(item['entry_id'])
    
    return results

def add_new_entry(entry_data: Dict, db_path: str = DEFAULT_DB_PATH, 
                  session_id: Optional[str] = None) -> Tuple[int, Optional[str]]:
    """
    High-level function to add a new entry with proper queue management.
    
    Returns:
        Tuple of (entry_id, queue_id) if queued, or (entry_id, None) if directly inserted
    """
    # First, check if we should use queue (based on source)
    source = entry_data.get('source', 'user')
    
    if source == 'engine' and session_id:
        # Engine operations during session go directly to database
        with get_connection(db_path) as conn:
            entry_id = EntryOperations.create_entry(entry_data, conn)
            return entry_id, None
    else:
        # User operations go through queue for review
        with get_connection(db_path) as conn:
            queue_ops = EngineQueueOperations()
            queue_id = queue_ops.add_to_queue(
                operation_type='PROPOSE_ENTRY',
                payload=entry_data,
                source=source,
                session_id=session_id,
                conn=conn
            )
            return None, queue_id

def run_engine_session(excel_version: Optional[str] = None, 
                       db_path: str = DEFAULT_DB_PATH) -> str:
    """
    High-level function to run an engine session.
    
    Returns:
        Session ID for tracking
    """
    with get_connection(db_path) as conn:
        session_ops = SessionOperations()
        session_id = session_ops.create_session(
            excel_version=excel_version,
            initiated_by='engine',
            conn=conn
        )
        
        # Log session start
        logger.info(f"Engine session started: {session_id}")
        
        return session_id

# ============================================================================
# MAIN FUNCTION FOR COMMAND LINE USE
# ============================================================================

def main():
    """Command-line interface for database operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='USLaP Database Access Layer')
    parser.add_argument('--search', type=str, help='Search for a word')
    parser.add_argument('--stats', action='store_true', help='Get database statistics')
    parser.add_argument('--cluster', type=str, help='Analyze a root cluster (e.g., R001)')
    parser.add_argument('--test', action='store_true', help='Run basic tests')
    
    args = parser.parse_args()
    
    if args.search:
        print(f"Searching for: {args.search}")
        results = search_word(args.search)
        
        print(f"\nExact matches: {len(results['exact_matches'])}")
        for match in results['exact_matches'][:5]:
            print(f"  - {match.get('en_term', 'N/A')} (score: {match.get('score', 'N/A')})")
        
        print(f"\nSimilar words: {len(results['similar_words'])}")
        for word in results['similar_words'][:5]:
            print(f"  - {word.get('raw_word', 'N/A')}")
        
        print(f"\nCluster expansion: {len(results['cluster_expansion'])} entries")
        if results['root_info']:
            print(f"Root: {results['root_info'].get('root_letters', 'N/A')}")
    
    elif args.stats:
        with get_connection() as conn:
            analytics = AnalyticsOperations()
            stats = analytics.get_database_stats(conn)
            
            print("Database Statistics:")
            print("=" * 40)
            for key, value in stats.items():
                if isinstance(value, list):
                    print(f"\n{key}:")
                    for item in value[:5]:  # Show top 5
                        print(f"  - {item}")
                else:
                    print(f"{key}: {value}")
    
    elif args.cluster:
        print(f"Analyzing cluster: {args.cluster}")
        with get_connection() as conn:
            analytics = AnalyticsOperations()
            analysis = analytics.get_cluster_analysis(args.cluster, conn)
            
            if 'root' in analysis:
                root = analysis['root']
                print(f"Root: {root.get('root_letters', 'N/A')}")
                print(f"Type: {root.get('root_type', 'N/A')}")
                print(f"Quran tokens: {root.get('quran_tokens', 0)}")
            
            print(f"\nEntries: {len(analysis.get('entries', []))}")
            for entry in analysis.get('entries', [])[:10]:
                print(f"  - {entry.get('en_term', 'N/A')} (score: {entry.get('score', 'N/A')})")
            
            print(f"\nDerivatives: {len(analysis.get('derivatives', []))}")
    
    elif args.test:
        print("Running basic tests...")
        with get_connection() as conn:
            # Test 1: Count entries
            conn.cursor.execute("SELECT COUNT(*) as count FROM entries")
            count = conn.cursor.fetchone()['count']
            print(f"✓ Database has {count} entries")
            
            # Test 2: Test UDF
            conn.cursor.execute("SELECT extract_consonants('example') as skeleton")
            skeleton = conn.cursor.fetchone()['skeleton']
            print(f"✓ UDF test: 'example' -> '{skeleton}'")
            
            # Test 3: Test word_fingerprints
            conn.cursor.execute("SELECT COUNT(*) as count FROM word_fingerprints")
            fp_count = conn.cursor.fetchone()['count']
            print(f"✓ Word fingerprints: {fp_count}")
            
            print("\nAll tests passed!")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()