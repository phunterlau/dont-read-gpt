async def handle_whoami(message, indexer=None, db_manager=None):
    """Handle !whoami command - show current Discord user information"""
    
    user = message.author
    user_id = str(user.id)
    username = user.name
    display_name = getattr(user, 'display_name', username)
    
    # Create a simple embed with user information
    import discord
    from datetime import datetime
    
    embed = discord.Embed(
        title="👤 User Information",
        color=0x2196F3  # Blue color
    )
    
    embed.add_field(name="Username", value=f"`{username}`", inline=True)
    embed.add_field(name="Display Name", value=f"`{display_name}`", inline=True)
    embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
    
    # Add avatar if available
    if hasattr(user, 'avatar') and user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    
    # Add account creation date if available
    if hasattr(user, 'created_at'):
        created_at = user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        embed.add_field(name="Account Created", value=created_at, inline=False)
    
    # Add some bot-specific information
    if db_manager:
        try:
            # Count user's documents in the database
            user_docs = db_manager.get_user_documents(user_id)
            doc_count = len(user_docs) if user_docs else 0
            embed.add_field(name="Documents in Database", value=f"`{doc_count}`", inline=True)
        except Exception:
            # If there's an error, just skip this info
            pass
    
    embed.set_footer(text=f"Requested at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await message.channel.send(embed=embed)
