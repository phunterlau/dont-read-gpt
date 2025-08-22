import discord
from datetime import datetime
import json

# --- Configuration ---
SUCCESS_COLOR = 0x4CAF50  # Green
ERROR_COLOR = 0xF44336    # Red
INFO_COLOR = 0x2196F3     # Blue
WARN_COLOR = 0xFFC107     # Amber

def create_error_embed(title: str, message: str, command: str = None, url: str = None) -> discord.Embed:
    """Creates a standardized error embed."""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=f"```{message}```",
        color=ERROR_COLOR
    )
    if command:
        embed.add_field(name="Command", value=f"`{command}`", inline=True)
    if url:
        embed.add_field(name="URL", value=url, inline=True)
    embed.set_footer(text=f"Error occurred at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return embed

def create_processing_embed(url: str) -> discord.Embed:
    """Creates an embed to show that a URL is being processed."""
    embed = discord.Embed(
        title="⏳ Processing URL...",
        description=f"Please wait while I fetch and analyze the content from:\n{url}",
        color=INFO_COLOR
    )
    return embed

def create_summary_embed(summary_json: str, url: str, doc_type: str, db_id: int, processing_time: float, is_updated: bool = False) -> discord.Embed:
    """Creates a rich embed from a structured JSON summary."""
    try:
        data = json.loads(summary_json)
    except (json.JSONDecodeError, TypeError):
        # Fallback for plain text summary
        return create_fallback_summary_embed(summary_json, url, doc_type, db_id, processing_time, is_updated)

    # Main embed setup
    title_prefix = "🔄 Updated: " if is_updated else "✅ New: "
    embed = discord.Embed(
        title=title_prefix + data.get("title", "Summary"),
        url=url,
        description=data.get("one_sentence_summary", "No one-sentence summary provided."),
        color=INFO_COLOR if is_updated else SUCCESS_COLOR
    )

    # Check if this is an arXiv academic paper format
    is_arxiv_format = all(key in data for key in ["main_point", "innovation", "contribution"])
    
    if is_arxiv_format:
        # ArXiv academic paper format
        main_point = data.get("main_point")
        if main_point:
            embed.add_field(name="📍 Main Point", value=main_point, inline=False)

        innovation = data.get("innovation")
        if innovation:
            embed.add_field(name="💡 Innovation", value=innovation, inline=False)

        contribution = data.get("contribution")
        if contribution:
            embed.add_field(name="🎯 Contribution", value=contribution, inline=False)

        improvement = data.get("improvement")
        if improvement:
            embed.add_field(name="📈 Improvement", value=improvement, inline=True)

        limitations = data.get("limitations")
        if limitations:
            embed.add_field(name="⚠️ Limitations", value=limitations, inline=True)

        insights = data.get("insights")
        if insights:
            embed.add_field(name="💭 Insights", value=insights, inline=False)

        one_line = data.get("one_line_summary")
        if one_line:
            embed.add_field(name="📝 Summary", value=f"*{one_line}*", inline=False)

        # Add personalized "Why You Should Read This" section if present
        why_read = data.get("why_you_should_read")
        if why_read:
            embed.add_field(name="🤔 Why You Should Read This", value=why_read, inline=False)

    else:
        # Regular format for non-arXiv content
        # Key Takeaways
        takeaways = data.get("key_takeaways", [])
        if takeaways:
            embed.add_field(
                name="Key Takeaways",
                value="\n".join([f"🔹 {item}" for item in takeaways]),
                inline=False
            )

        # Methodology
        methodology = data.get("methodology")
        if methodology:
            embed.add_field(name="Methodology", value=methodology, inline=False)

        # Results
        results = data.get("results")
        if results:
            embed.add_field(name="Results", value=results, inline=False)

        # Critique and Limitations
        critique = data.get("critique_and_limitations")
        if critique:
            embed.add_field(name="Critique & Limitations", value=critique, inline=False)

        # Confidence Score
        confidence = data.get("confidence_score")
        if confidence:
            embed.add_field(name="Confidence", value=f"{confidence * 100:.1f}%", inline=True)

    # Document Type with special emoji for arXiv
    doc_emoji = "📄" if is_arxiv_format else "📋"
    embed.add_field(name="Type", value=f"{doc_emoji} `{doc_type}`", inline=True)
    
    # Database ID
    embed.add_field(name="DB ID", value=f"`{db_id}`", inline=True)

    # Footer
    status_text = "Updated" if is_updated else "Processed"
    footer_text = f"{status_text} in {processing_time:.2f}s"
    if is_arxiv_format:
        footer_text += " • Academic Paper Analysis"
    footer_text += f" • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    embed.set_footer(text=footer_text)

    return embed

def create_fallback_summary_embed(summary_text: str, url: str, doc_type: str, db_id: int, processing_time: float, is_updated: bool = False) -> discord.Embed:
    """Creates a simple summary embed when structured data is not available."""
    title_prefix = "🔄 Updated: " if is_updated else "✅ New: "
    embed = discord.Embed(
        title=title_prefix + "Summary",
        url=url,
        description=summary_text,
        color=INFO_COLOR if is_updated else SUCCESS_COLOR
    )
    embed.add_field(name="Type", value=f"`{doc_type}`", inline=True)
    embed.add_field(name="DB ID", value=f"`{db_id}`", inline=True)
    status_text = "Updated" if is_updated else "Processed"
    embed.set_footer(text=f"{status_text} in {processing_time:.2f}s • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return embed

def create_existing_document_embed(document: dict, db_id: int) -> discord.Embed:
    """Creates an embed for an existing document that doesn't need updating - shows full content like create_summary_embed."""
    summary_json = document.get('summary', '{}')
    url = document.get('url', '')
    doc_type = document.get('type', 'unknown')
    
    try:
        data = json.loads(summary_json)
    except (json.JSONDecodeError, TypeError):
        # Fallback for plain text summary
        return create_fallback_existing_document_embed(summary_json, url, doc_type, db_id, document)

    # Main embed setup - similar to create_summary_embed but with "Found" prefix
    embed = discord.Embed(
        title="📋 Found: " + data.get("title", "Document"),
        url=url,
        description=data.get("one_sentence_summary", "No one-sentence summary provided."),
        color=WARN_COLOR
    )

    # Check if this is an arXiv academic paper format
    is_arxiv_format = all(key in data for key in ["main_point", "innovation", "contribution"])
    
    if is_arxiv_format:
        # ArXiv academic paper format - same as create_summary_embed
        main_point = data.get("main_point")
        if main_point:
            embed.add_field(name="📍 Main Point", value=main_point, inline=False)

        innovation = data.get("innovation")
        if innovation:
            embed.add_field(name="💡 Innovation", value=innovation, inline=False)

        contribution = data.get("contribution")
        if contribution:
            embed.add_field(name="🎯 Contribution", value=contribution, inline=False)

        improvement = data.get("improvement")
        if improvement:
            embed.add_field(name="📈 Improvement", value=improvement, inline=True)

        limitations = data.get("limitations")
        if limitations:
            embed.add_field(name="⚠️ Limitations", value=limitations, inline=True)

        insights = data.get("insights")
        if insights:
            embed.add_field(name="💭 Insights", value=insights, inline=False)

        one_line = data.get("one_line_summary")
        if one_line:
            embed.add_field(name="📝 Summary", value=f"*{one_line}*", inline=False)

        # Add personalized "Why You Should Read This" section if present
        why_read = data.get("why_you_should_read")
        if why_read:
            embed.add_field(name="🤔 Why You Should Read This", value=why_read, inline=False)

    else:
        # Regular format for non-arXiv content - same as create_summary_embed
        # Key Takeaways
        takeaways = data.get("key_takeaways", [])
        if takeaways:
            embed.add_field(
                name="Key Takeaways",
                value="\n".join([f"🔹 {item}" for item in takeaways]),
                inline=False
            )

        # Methodology
        methodology = data.get("methodology")
        if methodology:
            embed.add_field(name="Methodology", value=methodology, inline=False)

        # Results
        results = data.get("results")
        if results:
            embed.add_field(name="Results", value=results, inline=False)

        # Critique and Limitations
        critique = data.get("critique_and_limitations")
        if critique:
            embed.add_field(name="Critique & Limitations", value=critique, inline=False)

        # Confidence Score
        confidence = data.get("confidence_score")
        if confidence:
            embed.add_field(name="Confidence", value=f"{confidence * 100:.1f}%", inline=True)

    # Document Type with special emoji for arXiv
    doc_emoji = "📄" if is_arxiv_format else "📋"
    embed.add_field(name="Type", value=f"{doc_emoji} `{doc_type}`", inline=True)
    
    # Database ID
    embed.add_field(name="DB ID", value=f"`{db_id}`", inline=True)
    
    # Show when it was last updated
    updated_at = document.get('updated_at', document.get('created_at', 'Unknown'))
    embed.add_field(name="Last Updated", value=updated_at, inline=True)
    
    # Footer
    footer_text = f"Document already exists and is recent"
    if is_arxiv_format:
        footer_text += " • Academic Paper Analysis"
    footer_text += f" • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    embed.set_footer(text=footer_text)

    return embed

def create_fallback_existing_document_embed(summary_text: str, url: str, doc_type: str, db_id: int, document: dict) -> discord.Embed:
    """Creates a simple existing document embed when structured data is not available."""
    embed = discord.Embed(
        title="📋 Found: Document",
        url=url,
        description=summary_text[:500] + ("..." if len(summary_text) > 500 else ""),  # Show more text than before
        color=WARN_COLOR
    )
    embed.add_field(name="Type", value=f"`{doc_type}`", inline=True)
    embed.add_field(name="DB ID", value=f"`{db_id}`", inline=True)
    
    # Show when it was last updated
    updated_at = document.get('updated_at', document.get('created_at', 'Unknown'))
    embed.add_field(name="Last Updated", value=updated_at, inline=True)
    
    embed.set_footer(text=f"Document already exists and is recent • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return embed
