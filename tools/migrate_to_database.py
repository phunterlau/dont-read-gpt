#!/usr/bin/env python3
"""
Data Migration Tool for Discord Bot

This tool migrates all existing saved_text JSON files into the SQLite database.
It processes both the CSV index and individual JSON files to ensure complete data migration.

Usage:
    python tools/migrate_to_database.py [--dry-run] [--db-path path/to/db] [--saved-text-dir path/to/saved_text]

Examples:
    # Migrate all data with default paths
    python tools/migrate_to_database.py
    
    # Dry run to see what would be migrated
    python tools/migrate_to_database.py --dry-run
    
    # Use custom database path
    python tools/migrate_to_database.py --db-path custom_bot.db
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)

class DataMigrator:
    """Handles migration of saved_text data to SQLite database."""
    
    def __init__(self, db_path: str = "discord_bot.db", saved_text_dir: str = "saved_text"):
        self.db_path = db_path
        self.saved_text_dir = saved_text_dir
        self.db_manager = None
        self.stats = {
            'total_files_found': 0,
            'successful_migrations': 0,
            'failed_migrations': 0,
            'skipped_duplicates': 0,
            'errors': []
        }
    
    def initialize_database(self) -> bool:
        """Initialize the database connection."""
        try:
            self.db_manager = DatabaseManager(self.db_path)
            logger.info(f"Database initialized: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def find_all_json_files(self) -> List[str]:
        """Find all JSON files in the saved_text directory."""
        json_files = []
        saved_text_path = Path(self.saved_text_dir)
        
        if not saved_text_path.exists():
            logger.error(f"Saved text directory not found: {self.saved_text_dir}")
            return []
        
        # Recursively find all .json files
        for json_file in saved_text_path.rglob("*.json"):
            json_files.append(str(json_file))
        
        logger.info(f"Found {len(json_files)} JSON files")
        self.stats['total_files_found'] = len(json_files)
        return json_files
    
    def load_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            self.stats['errors'].append(f"Load error for {file_path}: {e}")
            return None
    
    def extract_document_data(self, data: Dict[str, Any], file_path: str) -> Optional[Tuple[Dict[str, Any], List[str], List[float]]]:
        """Extract document data for database insertion."""
        try:
            # Required fields
            url = data.get('url', '')
            doc_type = data.get('type', 'general')
            timestamp = float(data.get('timestamp', 0))
            
            if not url:
                logger.warning(f"No URL found in {file_path}")
                return None
            
            # Optional fields
            summary = data.get('summary', '')
            content = data.get('content', '')
            keywords = data.get('keywords', [])
            embeddings = data.get('embeddings', [])
            
            # Ensure keywords is a list
            if isinstance(keywords, str):
                keywords = [keywords]
            elif not isinstance(keywords, list):
                keywords = []
            
            # Ensure embeddings is a list
            if not isinstance(embeddings, list):
                embeddings = []
            
            # Create content preview (first 500 characters)
            content_preview = content[:500] if content else summary[:500] if summary else ''
            
            document_data = {
                'url': url,
                'doc_type': doc_type,
                'timestamp': timestamp,
                'summary': summary,
                'file_path': file_path,
                'content_preview': content_preview
            }
            
            return document_data, keywords, embeddings
            
        except Exception as e:
            logger.warning(f"Failed to extract data from {file_path}: {e}")
            self.stats['errors'].append(f"Extraction error for {file_path}: {e}")
            return None
    
    def migrate_file(self, file_path: str, dry_run: bool = False) -> bool:
        """Migrate a single JSON file to the database."""
        try:
            # Load the JSON data
            data = self.load_json_file(file_path)
            if not data:
                return False
            
            # Extract document data
            extraction_result = self.extract_document_data(data, file_path)
            if not extraction_result:
                return False
            
            document_data, keywords, embeddings = extraction_result
            
            if dry_run:
                logger.info(f"DRY RUN: Would migrate {document_data['url']} with {len(keywords)} keywords and {len(embeddings)} embeddings")
                return True
            
            # Check if document already exists
            existing_doc = self.db_manager.check_existing_document(document_data['url'])
            
            if existing_doc:
                logger.info(f"Document already exists: {document_data['url']} (ID: {existing_doc['id']})")
                self.stats['skipped_duplicates'] += 1
                return True
            
            # Add document to database
            doc_id = self.db_manager.add_document(
                url=document_data['url'],
                doc_type=document_data['doc_type'],
                timestamp=document_data['timestamp'],
                summary=document_data['summary'],
                file_path=document_data['file_path'],
                keywords=keywords,
                embedding=embeddings,
                content_preview=document_data['content_preview'],
                user_id=None  # Legacy data doesn't have user_id
            )
            
            if doc_id:
                logger.info(f"Successfully migrated: {document_data['url']} (ID: {doc_id})")
                self.stats['successful_migrations'] += 1
                return True
            else:
                logger.error(f"Failed to insert document: {document_data['url']}")
                self.stats['failed_migrations'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Migration failed for {file_path}: {e}")
            self.stats['errors'].append(f"Migration error for {file_path}: {e}")
            self.stats['failed_migrations'] += 1
            return False
    
    def migrate_all_files(self, dry_run: bool = False) -> bool:
        """Migrate all JSON files to the database."""
        logger.info(f"Starting migration {'(DRY RUN)' if dry_run else ''}")
        
        # Find all JSON files
        json_files = self.find_all_json_files()
        if not json_files:
            logger.error("No JSON files found to migrate")
            return False
        
        # Migrate each file
        for i, file_path in enumerate(json_files, 1):
            logger.info(f"Processing file {i}/{len(json_files)}: {os.path.basename(file_path)}")
            self.migrate_file(file_path, dry_run)
        
        return True
    
    def print_migration_stats(self):
        """Print migration statistics."""
        print("\n" + "="*50)
        print("MIGRATION STATISTICS")
        print("="*50)
        print(f"Total files found: {self.stats['total_files_found']}")
        print(f"Successful migrations: {self.stats['successful_migrations']}")
        print(f"Failed migrations: {self.stats['failed_migrations']}")
        print(f"Skipped duplicates: {self.stats['skipped_duplicates']}")
        print(f"Total errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nERRORS:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")
        
        print("="*50)
    
    def close(self):
        """Close database connection."""
        if self.db_manager:
            self.db_manager.close()

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Migrate saved_text JSON files to SQLite database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/migrate_to_database.py                    # Migrate all data
  python tools/migrate_to_database.py --dry-run         # See what would be migrated
  python tools/migrate_to_database.py --db-path custom.db   # Use custom database
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without actually doing it'
    )
    
    parser.add_argument(
        '--db-path',
        default='discord_bot.db',
        help='Path to SQLite database file (default: discord_bot.db)'
    )
    
    parser.add_argument(
        '--saved-text-dir',
        default='saved_text',
        help='Path to saved_text directory (default: saved_text)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create migrator
    migrator = DataMigrator(args.db_path, args.saved_text_dir)
    
    try:
        # Initialize database
        if not migrator.initialize_database():
            sys.exit(1)
        
        # Run migration
        success = migrator.migrate_all_files(args.dry_run)
        
        # Print statistics
        migrator.print_migration_stats()
        
        if success:
            print(f"\n✅ Migration {'simulation' if args.dry_run else ''} completed successfully!")
        else:
            print(f"\n❌ Migration {'simulation' if args.dry_run else ''} completed with errors.")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️ Migration interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    
    finally:
        migrator.close()

if __name__ == "__main__":
    main()
