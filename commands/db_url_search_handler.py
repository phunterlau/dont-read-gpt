import time
from database_manager import DatabaseManager

async def handle_db_url_search(message, db_manager: DatabaseManager = None):
    """Handle database URL search command: !dburl <pattern>"""
    if len(message.content.split(' ')) < 2:
        await message.channel.send('Usage: !dburl <url_pattern>')
        return
    
    if db_manager is None:
        db_manager = DatabaseManager()
    
    pattern = message.content.split(' ', 1)[1].strip()
    
    try:
        results = db_manager.search_by_url(pattern)
        
        if not results:
            await message.channel.send(f'🔗 No URLs found matching pattern: **{pattern}**')
            return
        
        # Limit results for Discord message
        limited_results = results[:5]
        response = f'🔗 **URL search results for "{pattern}" ({len(results)} found):**\n\n'
        
        for i, result in enumerate(limited_results, 1):
            # Format timestamp
            date_str = time.strftime('%Y-%m-%d', time.localtime(result['timestamp']))
            
            # Truncate URL if too long
            url = result['url']
            if len(url) > 80:
                url = url[:77] + '...'
            
            # Show summary (full summary)
            summary = result['summary']
            
            response += f"**{i}.** {url}\n"
            response += f"   📅 {date_str} | 🏷️ {result['type']}\n"
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
        await message.channel.send(f'❌ Error searching URLs: {str(e)}')
        print(f"Database URL search error: {e}")
