import discord
import arxiv
from commands.wget_handler import handle_wget

async def handle_find(message, indexer, db_manager):
    """
    Handle the !find command for searching arXiv papers by keyword.
    
    Usage: !find <keywords>
    Example: !find transformer architectures
    
    Searches arXiv for the top result matching the keywords and processes it
    through the existing wget pipeline.
    """
    
    # Extract keywords after !find
    content = message.content[5:].strip()  # Remove "!find" prefix
    
    if not content:
        embed = discord.Embed(
            title="🔍 arXiv Search Help",
            description="Search for the top arXiv paper matching your keywords.",
            color=0x3498db
        )
        embed.add_field(
            name="Usage",
            value="`!find <keywords>`",
            inline=False
        )
        embed.add_field(
            name="Examples",
            value="`!find transformer architectures`\n`!find machine learning optimization`\n`!find computer vision attention`",
            inline=False
        )
        embed.set_footer(text="Tip: No quotes needed for multi-word searches")
        await message.channel.send(embed=embed)
        return

    # Provide immediate feedback
    search_msg = await message.channel.send(f"🔎 Searching arXiv for: **{content}**...")

    try:
        # Search arXiv for the top result
        client = arxiv.Client()
        search = arxiv.Search(
            query=content,
            max_results=1,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        # Get the first (top) result using the client
        results = list(client.results(search))
        top_result = results[0] if results else None

        if not top_result:
            await search_msg.edit(content=f"❌ No arXiv papers found for: **{content}**\n\nTry different keywords or check spelling.")
            return

        # Found a paper - show what we found
        paper_url = top_result.entry_id
        paper_title = top_result.title
        paper_authors = ", ".join([str(author) for author in top_result.authors[:3]])  # First 3 authors
        if len(top_result.authors) > 3:
            paper_authors += " et al."
        
        # Clean the arXiv URL to remove version numbers that might cause issues
        clean_url = paper_url
        if 'arxiv.org' in paper_url:
            from readers.arxiv_reader import extract_arxiv_id
            arxiv_id = extract_arxiv_id(paper_url, include_version=False)
            if arxiv_id:
                clean_url = f"https://arxiv.org/abs/{arxiv_id}"
        
        await search_msg.edit(
            content=f"✅ **Top result found:**\n"
                   f"📄 **{paper_title}**\n"
                   f"👥 {paper_authors}\n"
                   f"🔗 {clean_url}\n\n"
                   f"⚡ Processing paper..."
        )

        # Create a modified message object to pass to wget handler
        # This preserves the original message context while changing the content
        class MockMessage:
            def __init__(self, original_message, new_content):
                # Copy all attributes from original message
                self.author = original_message.author
                self.channel = original_message.channel
                self.guild = original_message.guild
                self.id = original_message.id
                self.created_at = original_message.created_at
                # Set new content for wget processing
                self.content = new_content

        # Create mock message with the clean paper URL
        mock_message = MockMessage(message, clean_url)
        
        # Process the paper through existing wget pipeline
        # This will handle all the database lookup, summarization, personalization, etc.
        await handle_wget(mock_message, indexer, db_manager)

    except Exception as e:
        await search_msg.edit(
            content=f"❌ **Error searching arXiv:**\n"
                   f"```\n{str(e)}\n```\n"
                   f"Please try again or check your search terms."
        )
