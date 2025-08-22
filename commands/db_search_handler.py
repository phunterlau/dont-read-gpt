import time
from database_manager import DatabaseManager

async def handle_db_search(message, db_manager: DatabaseManager = None):
    """Handle database search command: !dbsearch <keyword>"""
    if len(message.content.split(' ')) < 2:
        await message.channel.send('Usage: !dbsearch <keyword>')
        return
    
    if db_manager is None:
        db_manager = DatabaseManager()
    
    keyword = message.content.split(' ', 1)[1].strip()
    
    try:
        results = db_manager.search_by_keyword(keyword)
        
        if not results:
            await message.channel.send(f'🔍 No results found for keyword: **{keyword}**')
            return
        
        # Limit results for Discord message
        limited_results = results[:5]
        response = f'🔍 **Search results for "{keyword}" ({len(results)} found):**\n\n'
        
        for i, result in enumerate(limited_results, 1):
            # Format timestamp
            date_str = time.strftime('%Y-%m-%d', time.localtime(result['timestamp']))
            
            # Truncate URL if too long
            url = result['url']
            if len(url) > 80:
                url = url[:77] + '...'
            
            # Show summary (full summary)
            summary = result['summary']
            
            # Show first few keywords
            keywords = ', '.join(result['keywords'][:4])
            if len(result['keywords']) > 4:
                keywords += f' (+{len(result["keywords"])-4} more)'
            
            response += f"**{i}.** {url}\n"
            response += f"   📅 {date_str} | 🏷️ {result['type']}\n"
            response += f"   🔑 {keywords}\n"
            response += f"   📝 {summary}\n\n"
        
        if len(results) > 5:
            response += f"... and {len(results) - 5} more results.\n"
        
        # Split message if too long
        if len(response) > 2000:
            parts = response.split('\n\n')
            current_part = ""
            for part in parts:
                if len(current_part + part) < 1900:
                    current_part += part + '\n\n'
                else:
                    await message.channel.send(current_part)
                    current_part = part + '\n\n'
            if current_part:
                await message.channel.send(current_part)
        else:
            await message.channel.send(response)
            
    except Exception as e:
        await message.channel.send(f'❌ Error searching database: {str(e)}')
        print(f"Database search error: {e}")
