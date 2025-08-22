import json
import time
from indexer import Indexer
from database_manager import DatabaseManager

async def handle_tail(message, indexer: Indexer, db_manager: DatabaseManager):
    """Handle !tail command - show the user's recent 3 added items from both systems"""
    
    try:
        user_id = str(message.author.id)  # Get user ID for filtering
        
        # Get recent documents from both sources (user-filtered for database)
        legacy_stats = indexer.get_stats()  # Legacy system doesn't support user filtering yet
        db_stats = db_manager.get_stats(user_id=user_id)  # Filter by user
        
        # Combine recent documents
        all_recent = []
        
        # Add legacy recent documents (these are shared among all users)
        for doc in legacy_stats.get('recent_documents', []):
            all_recent.append({
                'url': doc['url'],
                'timestamp': doc.get('timestamp', 0),
                'type': doc.get('type', 'unknown'),
                'id': doc.get('id', 'N/A'),
                'source': 'legacy (shared)'
            })
        
        # Add database recent documents (user-specific)
        for doc in db_stats.get('recent_documents', []):
            all_recent.append({
                'url': doc['url'],
                'timestamp': doc.get('timestamp', 0),
                'type': doc.get('type', 'unknown'),
                'id': doc.get('id', 'N/A'),
                'source': 'database (yours)'
            })
        
        if not all_recent:
            await message.channel.send('📭 You don\'t have any recent documents yet.\nUse `!wget <url>` to add your first document!')
            return
        
        # Sort by timestamp (most recent first) and get top 3
        all_recent.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_3 = all_recent[:3]
        
        response = "📋 **Your Recent 3 Added Items**\n"
        response += "*Note: Legacy documents are shared among all users*\n"
        response += "=" * 40 + "\n\n"
        
        for i, doc in enumerate(recent_3, 1):
            # Format timestamp
            try:
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(doc['timestamp']))
            except (ValueError, OSError):
                date_str = 'Unknown date'
            
            # Truncate URL if too long
            url = doc['url']
            if len(url) > 70:
                url = url[:67] + '...'
            
            # Add emoji based on source
            emoji = "🆕" if "yours" in doc['source'] else "📚"
            
            response += f"{emoji} **{i}.** {url}\n"
            response += f"   📅 {date_str}\n"
            response += f"   🏷️ Type: {doc['type']}\n"
            response += f"   🔢 ID: {doc['id']} ({doc['source']})\n\n"
        
        # Add command suggestions
        response += "💡 **Try these commands:**\n"
        response += "   • `!grep <term>` - Search your content\n"
        response += "   • `!egrep <keyword>` - Search your keywords\n"
        response += "   • `!wget <url>` - Add new content\n"
        response += "   • `!stats` - View your statistics\n"
        
        await message.channel.send(response[:2000])
        
    except Exception as e:
        await message.channel.send(f'❌ Error getting your recent items: {str(e)}')
        print(f"Tail error: {e}")
        
    return
