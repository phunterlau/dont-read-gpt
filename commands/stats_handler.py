import os
from indexer import Indexer
from database_manager import DatabaseManager

async def handle_stats(message, indexer: Indexer, db_manager: DatabaseManager):
    """Handle !stats command - show user-specific statistics from both legacy and database sources"""
    
    try:
        user_id = str(message.author.id)  # Get user ID for filtering
        
        # Get stats from both sources (user-filtered for database)
        legacy_stats = indexer.get_stats()  # Legacy system doesn't have user filtering yet
        db_stats = db_manager.get_stats(user_id=user_id)  # Filter by user
        
        response = f"📊 **Your Personal Statistics**\n"
        response += "=" * 40 + "\n\n"
        
        # User-specific document counts
        total_legacy = legacy_stats['total_documents']  # All legacy docs for now
        total_db = db_stats['total_documents']  # User's DB docs only
        total_user_db = total_db  # User's total in DB
        
        response += f"📚 **Your documents:** {total_user_db}\n"
        response += f"   • Your database documents: {total_db}\n"
        if total_legacy > 0:
            response += f"   • Legacy system (shared): {total_legacy}\n"
        response += "\n"
        
        # User-specific keyword counts  
        total_db_keywords = db_stats['total_keywords']
        unique_db_keywords = db_stats['unique_keywords']
        
        response += f"🔑 **Your keywords:**\n"
        if total_db_keywords > 0:
            response += f"   • Total: {total_db_keywords} ({unique_db_keywords} unique)\n"
        else:
            response += f"   • No keywords yet - add some documents!\n"
        response += "\n"
        
        # User's document types
        response += "📂 **Your documents by type:**\n"
        if db_stats['documents_by_type']:
            for doc_type, count in sorted(db_stats['documents_by_type'].items()):
                response += f"   • {doc_type}: {count}\n"
        else:
            response += "   • No documents yet\n"
        response += "\n"
        
        # User's top keywords
        if db_stats['top_keywords']:
            response += "🔥 **Your top keywords:**\n"
            for keyword, count in list(db_stats['top_keywords'].items())[:5]:
                response += f"   • {keyword}: {count}\n"
            response += "\n"
        
        # User's recent documents
        if db_stats['recent_documents']:
            response += "📅 **Your recent documents:**\n"
            for i, doc in enumerate(db_stats['recent_documents'][:3], 1):
                url = doc['url']
                if len(url) > 60:
                    url = url[:57] + '...'
                response += f"   {i}. {url}\n"
        else:
            response += "📅 **No recent documents**\n"
            response += "   Use `!wget <url>` to add your first document!\n"
        
        # System info
        db_path = db_manager.db_path
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            response += f"\n💾 **Database size:** {size_mb:.2f} MB\n"
        
        response += "\n🔧 **Available commands:**\n"
        response += "   • `!grep <term>` - Text search\n"
        response += "   • `!egrep <keyword>` - Keyword search\n"
        response += "   • `!wget <url>` - Add content\n"
        response += "   • `!tail` - Recent additions\n"
        response += "   • `!stats` - This overview\n"
        
        await message.channel.send(response[:2000])
        
    except Exception as e:
        await message.channel.send(f'❌ Error getting statistics: {str(e)}')
        print(f"Stats error: {e}")
