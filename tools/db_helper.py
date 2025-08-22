#!/usr/bin/env python3
"""
Helper script for database operations

This script provides convenient commands for managing the Discord bot database.

Usage:
    python tools/db_helper.py [command] [options]

Commands:
    migrate          - Migrate all saved_text files to database
    stats            - Show database statistics
    search <query>   - Search documents by keyword
    list-types       - List all document types
    backup           - Create database backup
    verify           - Verify database integrity

Examples:
    python tools/db_helper.py migrate
    python tools/db_helper.py stats
    python tools/db_helper.py search "machine learning"
    python tools/db_helper.py list-types
"""

import os
import sys
import argparse
import shutil
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from database_manager import DatabaseManager

def show_stats(db_path="discord_bot.db"):
    """Show database statistics."""
    db = DatabaseManager(db_path)
    try:
        stats = db.get_stats()
        print("\n📊 DATABASE STATISTICS")
        print("=" * 50)
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total keywords: {stats['total_keywords']}")
        print(f"Unique keywords: {stats['unique_keywords']}")
        
        print(f"\nDocuments by type:")
        for doc_type, count in stats['documents_by_type'].items():
            print(f"  {doc_type}: {count}")
        
        print(f"\nTop keywords:")
        for keyword, count in list(stats['top_keywords'].items())[:5]:
            print(f"  {keyword}: {count}")
        
        print(f"\nRecent documents:")
        for doc in stats['recent_documents'][:3]:
            print(f"  {doc['url'][:60]}..." if len(doc['url']) > 60 else f"  {doc['url']}")
        
        print(f"\nDatabase file: {db_path}")
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"Database size: {size_mb:.2f} MB")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    finally:
        db.close()

def search_documents(query, db_path="discord_bot.db", limit=10):
    """Search documents by keyword."""
    db = DatabaseManager(db_path)
    try:
        results = db.search_by_keyword(query)
        
        print(f"\n🔍 SEARCH RESULTS for '{query}'")
        print("=" * 50)
        print(f"Found {len(results)} documents")
        
        for i, doc in enumerate(results[:limit], 1):
            print(f"\n{i}. {doc['url']}")
            print(f"   Type: {doc['type']}")
            print(f"   Summary: {doc['summary'][:100]}..." if doc['summary'] else "   No summary")
            print(f"   Keywords: {', '.join(doc['keywords'][:5])}" + ("..." if len(doc['keywords']) > 5 else ""))
        
        if len(results) > limit:
            print(f"\n... and {len(results) - limit} more results")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error searching: {e}")
    finally:
        db.close()

def search_by_url(pattern, db_path="discord_bot.db", limit=10):
    """Search documents by URL pattern."""
    db = DatabaseManager(db_path)
    try:
        results = db.search_by_url(pattern)
        
        print(f"\n🔗 URL SEARCH RESULTS for '{pattern}'")
        print("=" * 50)
        print(f"Found {len(results)} documents")
        
        for i, doc in enumerate(results[:limit], 1):
            print(f"\n{i}. {doc['url']}")
            print(f"   Type: {doc['type']}")
            print(f"   Date: {doc['timestamp']}")
            print(f"   Summary: {doc['summary'][:100]}..." if doc['summary'] else "   No summary")
        
        if len(results) > limit:
            print(f"\n... and {len(results) - limit} more results")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error searching URLs: {e}")
    finally:
        db.close()

def list_document_types(db_path="discord_bot.db"):
    """List all document types in the database."""
    db = DatabaseManager(db_path)
    try:
        stats = db.get_stats()
        
        print("\n📑 DOCUMENT TYPES")
        print("=" * 50)
        for doc_type, count in sorted(stats['documents_by_type'].items()):
            print(f"{doc_type:15} {count:6} documents")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error listing types: {e}")
    finally:
        db.close()

def backup_database(db_path="discord_bot.db"):
    """Create a backup of the database."""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        
        # Show backup size
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"   Backup size: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")

def verify_database(db_path="discord_bot.db"):
    """Verify database integrity."""
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    db = DatabaseManager(db_path)
    try:
        # Test basic operations
        stats = db.get_stats()
        print(f"✅ Database accessible")
        print(f"✅ Found {stats['total_documents']} documents")
        
        # Test search
        test_results = db.search_by_keyword("test")
        print(f"✅ Search functionality working")
        
        # Test document retrieval
        if stats['total_documents'] > 0:
            doc = db.get_document_by_id(1)
            if doc:
                print(f"✅ Document retrieval working")
            else:
                print(f"⚠️  Could not retrieve document ID 1")
        
        print(f"✅ Database verification completed successfully")
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
    finally:
        db.close()

def rebuild_database(db_path="discord_bot.db"):
    """Rebuild database from scratch."""
    print(f"🔄 REBUILDING DATABASE: {db_path}")
    print("=" * 50)
    
    # Backup existing database if it exists
    if os.path.exists(db_path):
        print(f"📋 Creating backup of existing database...")
        backup_database(db_path)
        print(f"🗑️  Removing old database...")
        os.remove(db_path)
    
    # Create fresh database
    print(f"🆕 Creating fresh database...")
    db = DatabaseManager(db_path)
    db.close()
    print(f"✅ New database created: {db_path}")
    
    # Run migration
    print(f"📥 Running migration from saved_text...")
    run_migration()
    
    print(f"✅ Database rebuild completed!")
    
    # Show final stats
    show_stats(db_path)

def show_help():
    """Display help information."""
    print("""
🛠️  Discord Bot Database Helper
==================================================

COMMANDS:
  migrate      - Run migration to load saved_text files into database
  stats        - Show database statistics
  search       - Search documents by keyword
  search-url   - Search documents by URL pattern
  list-types   - List all document types in database
  backup       - Create a backup of the database
  verify       - Verify database integrity
  rebuild      - Rebuild database from scratch (with backup)

EXAMPLES:
  python tools/db_helper.py stats
  python tools/db_helper.py search "machine learning"
  python tools/db_helper.py search-url github.com
  python tools/db_helper.py search "AI" --limit 5
  python tools/db_helper.py backup
  python tools/db_helper.py verify

OPTIONS:
  --db-path    - Specify database file path (default: discord_bot.db)
  --limit      - Limit search results (default: 10)

DATABASE INFO:
  The database contains documents, keywords, and embeddings
  Documents are automatically categorized by type (arxiv, github, etc.)
  Search supports partial keyword matching
  URL search supports pattern matching

==================================================
""")

def run_migration():
    """Run the migration tool."""
    import subprocess
    try:
        result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'migrate_to_database.py')
        ], check=True)
        print("✅ Migration completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Database helper for Discord bot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', choices=['migrate', 'stats', 'search', 'search-url', 'list-types', 'backup', 'verify', 'rebuild', 'help'],
                       help='Command to execute')
    parser.add_argument('query', nargs='?', help='Search query (for search command)')
    parser.add_argument('--db-path', default='discord_bot.db', help='Database file path')
    parser.add_argument('--limit', type=int, default=10, help='Limit search results')
    
    args = parser.parse_args()
    
    if args.command == 'migrate':
        run_migration()
    elif args.command == 'stats':
        show_stats(args.db_path)
    elif args.command == 'search':
        if not args.query:
            print("❌ Search command requires a query. Example: python tools/db_helper.py search 'machine learning'")
            sys.exit(1)
        search_documents(args.query, args.db_path, args.limit)
    elif args.command == 'search-url':
        if not args.query:
            print("❌ URL search command requires a pattern. Example: python tools/db_helper.py search-url github.com")
            sys.exit(1)
        search_by_url(args.query, args.db_path, args.limit)
    elif args.command == 'list-types':
        list_document_types(args.db_path)
    elif args.command == 'backup':
        backup_database(args.db_path)
    elif args.command == 'verify':
        verify_database(args.db_path)
    elif args.command == 'rebuild':
        rebuild_database(args.db_path)
    elif args.command == 'help':
        show_help()

if __name__ == "__main__":
    main()
