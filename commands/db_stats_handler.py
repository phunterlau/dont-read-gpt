import os
from database_manager import DatabaseManager

async def handle_db_stats(message, db_manager: DatabaseManager = None):
    """Handle database stats command: !dbstats"""
    
    if db_manager is None:
        db_manager = DatabaseManager()
    
    try:
        stats = db_manager.get_stats()
        
        response = "📊 **Database Statistics**\n"
        response += "=" * 30 + "\n\n"
        
        # Basic stats
        response += f"📚 **Total documents:** {stats['total_documents']}\n"
        response += f"🔑 **Total keywords:** {stats['total_keywords']}\n"
        response += f"🏷️ **Unique keywords:** {stats['unique_keywords']}\n\n"
        
        # Documents by type
        response += "📂 **Documents by type:**\n"
        for doc_type, count in stats['documents_by_type'].items():
            response += f"   • {doc_type}: {count}\n"
        response += "\n"
        
        # Top keywords
        response += "🔥 **Top keywords:**\n"
        for keyword, count in list(stats['top_keywords'].items())[:5]:
            response += f"   • {keyword}: {count}\n"
        response += "\n"
        
        # Recent documents
        response += "📅 **Recent documents:**\n"
        for i, doc in enumerate(stats['recent_documents'][:3], 1):
            url = doc['url']
            if len(url) > 60:
                url = url[:57] + '...'
            response += f"   {i}. {url}\n"
        
        # Database file info
        db_path = db_manager.db_path
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            response += f"\n💾 **Database size:** {size_mb:.2f} MB\n"
        
        await message.channel.send(response)
        
    except Exception as e:
        await message.channel.send(f'❌ Error getting database stats: {str(e)}')
        print(f"Database stats error: {e}")
