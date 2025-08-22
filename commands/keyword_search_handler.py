import time
from indexer import Indexer
from database_manager import DatabaseManager

async def handle_keyword_search(message, indexer: Indexer, db_manager: DatabaseManager):
    """Handle !egrep command - case insensitive keyword search across both legacy and database sources"""
    if len(message.content.split(' ')) < 2:
        await message.channel.send('Usage: !egrep <keyword>')
        return
    
    keyword = message.content.split(' ', 1)[1].strip()
    user_id = str(message.author.id)  # Get user ID for filtering
    
    # Search both legacy indexer and database (user-filtered)
    legacy_results = indexer.search_by_keyword(keyword)  # Legacy indexer doesn't have user filtering yet
    db_results = db_manager.search_by_keyword(keyword, user_id=user_id)  # Filter by user
    
    # Combine and deduplicate results by URL
    all_results = []
    seen_urls = set()
    
    # Add legacy results (filter by user_id if available in legacy data)
    for result in legacy_results:
        # For now, legacy results don't have user filtering, so we include them
        # In a future phase, we can add user filtering to the legacy indexer
        if result['url'] not in seen_urls:
            doc = indexer.get_document_by_id(result['id'])
            all_results.append({
                'url': result['url'],
                'type': result['type'],
                'timestamp': result['timestamp'],
                'summary': result['summary'],
                'keywords': doc['keywords'],
                'source': 'legacy'
            })
            seen_urls.add(result['url'])
    
    # Add database results (already filtered by user)
    for result in db_results:
        if result['url'] not in seen_urls:
            all_results.append({
                'url': result['url'],
                'type': result['type'],
                'timestamp': result['timestamp'],
                'summary': result['summary'],
                'keywords': result['keywords'],
                'source': 'database'
            })
            seen_urls.add(result['url'])
    
    if not all_results:
        await message.channel.send(f'🔑 No documents found with keyword: **{keyword}**\n*Note: Only your documents are searched*')
        return
    
    # Sort by timestamp (most recent first)
    all_results.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit results for Discord message
    limited_results = all_results[:5]
    response = f'🔑 **Your keyword search results for "{keyword}" ({len(all_results)} found):**\n\n'
    
    for i, result in enumerate(limited_results, 1):
        # Format timestamp
        date_str = time.strftime('%Y-%m-%d', time.localtime(result['timestamp']))
        
        # Truncate URL if too long
        url = result['url']
        if len(url) > 80:
            url = url[:77] + '...'
        
        # Show summary (full summary)
        summary = result['summary']
        
        # Show first few keywords, highlighting the searched keyword
        keywords_list = result['keywords'] if result['keywords'] else []
        keywords_display = []
        for kw in keywords_list[:4]:
            if keyword.lower() in kw.lower():
                keywords_display.append(f"**{kw}**")  # Bold matching keywords
            else:
                keywords_display.append(kw)
        
        keywords = ', '.join(keywords_display) if keywords_display else 'No keywords'
        if len(keywords_list) > 4:
            keywords += f' (+{len(keywords_list)-4} more)'
        
        response += f"**{i}.** {url}\n"
        response += f"   📅 {date_str} | 🏷️ {result['type']}\n"
        response += f"   🔑 {keywords}\n"
        response += f"   📝 {summary}\n\n"
    
    if len(all_results) > 5:
        response += f"... and {len(all_results) - 5} more results.\n"
    
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
