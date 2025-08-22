async def handle_db_help(message):
    """Handle database help command: !dbhelp"""
    
    help_text = """🛠️ **Database Commands Help**
==========================================

**Search Commands:**
🔍 `!dbsearch <keyword>` - Search documents by keyword
🔗 `!dburl <pattern>` - Search documents by URL pattern
📊 `!dbstats` - Show database statistics

**Examples:**
```
!dbsearch machine learning
!dbsearch "AI models"
!dburl github.com
!dburl arxiv.org
!dbstats
```

**Features:**
• Search through all migrated documents (81 docs)
• Keyword matching with partial support
• URL pattern matching
• Results show keywords, summaries, and dates
• Limited to 5 results per search for readability

**Original Commands Still Available:**
• `!search` - Legacy text search
• `!keyword` - Legacy keyword search  
• `!stats` - Legacy statistics
• `!wget <url>` - Add new documents

==========================================
Type `!dbhelp` anytime to see this help."""

    await message.channel.send(help_text)
