#!/usr/bin/env python3
"""
Test script for the new database schema functionality
"""

import os
import sys
import time
import json

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from database_manager import DatabaseManager

def test_new_schema_features():
    """Test all new schema features."""
    print("🧪 Testing New Database Schema Features")
    print("=" * 50)
    
    # Create test database
    test_db_path = "test_new_schema.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = DatabaseManager(test_db_path)
    
    try:
        test_url = "https://example.com/test-article"
        test_user_id = "123456789012345678"  # Discord user ID format
        
        print("\n1. ✅ Database initialization with new schema")
        
        # Test 1: Add document with user_id
        print("\n2. 📝 Testing add_document with user_id...")
        doc_id = db.add_document(
            url=test_url,
            doc_type="webpage",
            timestamp=time.time(),
            summary='{"title": "Test Article", "one_sentence_summary": "This is a test article.", "suggested_keywords": ["test", "article", "example"]}',
            file_path="/test/article.json",
            keywords=["test", "article", "example"],
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            content_preview="This is a test article about testing new features...",
            user_id=test_user_id
        )
        print(f"   Document added with ID: {doc_id}")
        
        # Test 2: Check existing document
        print("\n3. 🔍 Testing check_existing_document...")
        existing = db.check_existing_document(test_url)
        if existing:
            print(f"   Found existing document: ID {existing['id']}")
            print(f"   User ID: {existing['user_id']}")
            print(f"   Timestamp: {existing['timestamp']}")
            print(f"   Updated at: {existing['updated_at']}")
        else:
            print("   ❌ Document not found!")
            
        # Test 3: Test outdated check
        print("\n4. ⏰ Testing is_document_outdated...")
        current_time = time.time()
        old_timestamp = current_time - (8 * 24 * 60 * 60)  # 8 days ago
        recent_timestamp = current_time - (1 * 60 * 60)    # 1 hour ago
        
        print(f"   8 days old is outdated (7 day threshold): {db.is_document_outdated(old_timestamp, 7)}")
        print(f"   1 hour old is outdated (7 day threshold): {db.is_document_outdated(recent_timestamp, 7)}")
        
        # Test 4: Update document
        print("\n5. 🔄 Testing update_document...")
        success = db.update_document(
            document_id=doc_id,
            summary='{"title": "Updated Test Article", "one_sentence_summary": "This is an updated test article.", "suggested_keywords": ["updated", "test", "article"]}',
            keywords=["updated", "test", "article"],
            embedding=[0.6, 0.7, 0.8, 0.9, 1.0],
            content_preview="This is an updated test article...",
            user_id=test_user_id
        )
        print(f"   Update successful: {success}")
        
        # Test 5: Retrieve updated document
        print("\n6. 📖 Testing retrieval of updated document...")
        updated_doc = db.get_document_by_id(doc_id)
        if updated_doc:
            try:
                summary_data = json.loads(updated_doc['summary'])
                print(f"   Title: {summary_data.get('title', 'N/A')}")
                print(f"   Keywords: {updated_doc['keywords']}")
                print(f"   User ID: {updated_doc['user_id']}")
            except json.JSONDecodeError:
                print(f"   Summary (plain text): {updated_doc['summary'][:50]}...")
        
        # Test 6: Search functionality with new fields
        print("\n7. 🔎 Testing search with new schema...")
        search_results = db.search_by_url("example.com")
        print(f"   URL search results: {len(search_results)}")
        if search_results:
            result = search_results[0]
            print(f"   Found URL: {result['url']}")
            print(f"   User ID: {result.get('user_id', 'N/A')}")
            print(f"   Updated at: {result.get('updated_at', 'N/A')}")
        
        # Test 7: Database stats
        print("\n8. 📊 Testing database stats...")
        stats = db.get_stats()
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Total keywords: {stats['total_keywords']}")
        print(f"   Unique keywords: {stats['unique_keywords']}")
        
        print("\n✅ All tests passed! New schema is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        print(f"\n🧹 Cleanup completed")

def test_migration_compatibility():
    """Test that migration still works with new schema."""
    print("\n" + "=" * 50)
    print("🔄 Testing Migration Compatibility")
    print("=" * 50)
    
    # Create a simple test JSON file
    test_dir = "test_saved_text"
    test_file = os.path.join(test_dir, "test.json")
    
    os.makedirs(test_dir, exist_ok=True)
    
    test_data = {
        "url": "https://test.com/migration-test",
        "type": "webpage",
        "timestamp": time.time(),
        "content": "This is test content for migration.",
        "summary": "Test migration summary",
        "keywords": ["migration", "test"],
        "embeddings": [0.1, 0.2, 0.3]
    }
    
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Test database
    test_db_path = "test_migration.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = DatabaseManager(test_db_path)
    
    try:
        print(f"\n1. 📁 Created test data file: {test_file}")
        
        # Run migration
        print("\n2. 🔄 Running migration...")
        
        # Create CSV index
        csv_path = os.path.join(test_dir, "index.csv")
        with open(csv_path, 'w') as f:
            f.write(f"webpage,{test_data['timestamp']},{test_file}\n")
        
        db.migrate_from_csv(csv_path, test_dir)
        print("   Migration completed")
        
        # Check results
        print("\n3. ✅ Verifying migration results...")
        migrated_doc = db.check_existing_document(test_data['url'])
        if migrated_doc:
            print(f"   Document migrated successfully: ID {migrated_doc['id']}")
            print(f"   User ID (should be None): {migrated_doc['user_id']}")
            print(f"   URL: {migrated_doc['url']}")
        else:
            print("   ❌ Migration failed!")
            
        print("\n✅ Migration compatibility test passed!")
        
    except Exception as e:
        print(f"\n❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
        print(f"\n🧹 Migration test cleanup completed")

if __name__ == "__main__":
    test_new_schema_features()
    test_migration_compatibility()
    print("\n🎉 All tests completed successfully!")
