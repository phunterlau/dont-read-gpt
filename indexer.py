import os
import json
import glob
import re
from datetime import datetime
from database_manager import DatabaseManager

class Indexer:
    def __init__(self, db_path: str = "discord_bot.db", auto_migrate: bool = False):
        """
        Initialize the indexer with a SQLite database path.
        
        Args:
            db_path (str): Path to the SQLite database file
            auto_migrate (bool): Whether to automatically migrate existing CSV data to database
        """
        self.db_manager = DatabaseManager(db_path)
        # Migrate data from old CSV system if it exists and auto_migrate is enabled
        if auto_migrate:
            self._migrate_existing_data()
    
    def _migrate_existing_data(self):
        """Migrate data from the old CSV index system if it exists."""
        csv_path = "saved_text/index.csv"
        if os.path.exists(csv_path):
            print("Migrating existing data from CSV index...")
            self.db_manager.migrate_from_csv(csv_path, "saved_text")
            print("Migration completed.")
    
    def close(self):
        """Close the database connection."""
        self.db_manager.close()
    
    def index_file(self, file_path):
        """
        Index a single JSON file.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            bool: True if indexing was successful, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract data from the JSON file
            url = data.get('url', '')
            doc_type = data.get('type', 'general')
            timestamp = float(data.get('timestamp', 0))
            content = data.get('content', '')
            summary = data.get('summary', '')
            keywords = data.get('keywords', [])
            embeddings = data.get('embeddings', [])
            
            # Extract content preview (first 500 chars)
            content_preview = ""
            if isinstance(content, str):
                content_preview = content[:500]
            elif isinstance(summary, str):
                content_preview = summary[:500]
            
            # Extract Obsidian keywords from obsidian_markdown if available
            obsidian_markdown = data.get('obsidian_markdown', '')
            obsidian_keywords = []
            if obsidian_markdown:
                obsidian_keywords = re.findall(r'\[\[(.*?)\]\]', obsidian_markdown)
            
            # Use obsidian_keywords if available, otherwise use the original keywords
            final_keywords = obsidian_keywords if obsidian_keywords else keywords
            
            # Add document to database
            document_id = self.db_manager.add_document(
                url=url,
                doc_type=doc_type,
                timestamp=timestamp,
                summary=summary,
                file_path=file_path,
                keywords=final_keywords,
                embedding=embeddings,
                content_preview=content_preview
            )
            
            return True
        
        except Exception as e:
            print(f"Error indexing file {file_path}: {str(e)}")
            return False
    
    def index_all_files(self, directory="saved_text"):
        """
        Index all JSON files in the specified directory and its subdirectories.
        
        Args:
            directory (str): Directory containing the JSON files
            
        Returns:
            tuple: (total_files, indexed_files) - counts of total and successfully indexed files
        """
        # Find all JSON files in the directory and its subdirectories
        json_files = glob.glob(os.path.join(directory, "**/*.json"), recursive=True)
        
        # Filter out index.csv and other non-content files
        json_files = [f for f in json_files if not f.endswith('index.csv')]
        
        total_files = len(json_files)
        indexed_files = 0
        
        for file_path in json_files:
            if self.index_file(file_path):
                indexed_files += 1
        
        return total_files, indexed_files
    
    def search_by_keyword(self, keyword, limit=10):
        """
        Search for documents containing the specified keyword.
        
        Args:
            keyword (str): Keyword to search for
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of dictionaries containing document information
        """
        return self.db_manager.search_by_keyword(keyword)[:limit]
    
    def search_by_text(self, query, limit=10):
        """
        Search for documents containing the specified text in content or summary.
        
        Args:
            query (str): Text to search for
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of dictionaries containing document information
        """
        # For now, use keyword search as a fallback for text search
        # In the future, this could be enhanced with full-text search
        return self.search_by_keyword(query, limit)
    
    def get_document_by_id(self, document_id):
        """
        Get a document by its ID.
        
        Args:
            document_id (int): Document ID
            
        Returns:
            dict: Document information
        """
        return self.db_manager.get_document_by_id(document_id)
    
    def get_related_documents(self, document_id, limit=5):
        """
        Get documents related to the specified document based on shared keywords.
        
        Args:
            document_id (int): Document ID
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of dictionaries containing related document information
        """
        return self.db_manager.get_related_documents(document_id, limit)
    
    def get_stats(self):
        """
        Get statistics about the indexed documents.
        
        Returns:
            dict: Statistics about the indexed documents
        """
        return self.db_manager.get_stats()


if __name__ == "__main__":
    # Test the indexer
    indexer = Indexer()
    total, indexed = indexer.index_all_files()
    print(f"Indexed {indexed} out of {total} files")
    
    # Print some stats
    stats = indexer.get_stats()
    print(f"Total documents: {stats['total_documents']}")
    print(f"Documents by type: {stats['documents_by_type']}")
    print(f"Total keywords: {stats['total_keywords']}")
    print(f"Unique keywords: {stats['unique_keywords']}")
    print(f"Top keywords: {stats['top_keywords']}")
    
    # Test search
    results = indexer.search_by_keyword("machine learning")
    print(f"Found {len(results)} documents with keyword 'machine learning'")
    
    indexer.close()
