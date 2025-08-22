import discord
from database_manager import DatabaseManager
from ai_func import process_user_memory

async def handle_mem(message, indexer, db_manager: DatabaseManager):
    """
    Handle the !mem command for storing and updating user research preferences.
    
    Usage:
    !mem <research interest text>  - Add/update research interest
    !mem --show                    - Show current memory profile
    !mem --clear                   - Clear memory profile
    """
    
    # Extract the content after !mem
    content = message.content[4:].strip()  # Remove "!mem" prefix
    user_id = str(message.author.id)
    
    # Handle special commands
    if content == "--show":
        return await show_user_memory(message, db_manager, user_id)
    elif content == "--clear":
        return await clear_user_memory(message, db_manager, user_id)
    elif not content:
        return await send_mem_help(message)
    
    # Process the new memory input
    await process_new_memory(message, db_manager, user_id, content)

async def process_new_memory(message, db_manager: DatabaseManager, user_id: str, new_memory: str):
    """Process and store a new memory input."""
    try:
        # Send initial processing message
        processing_msg = await message.channel.send("🧠 Processing your research preferences...")
        
        # Get existing memory profile
        existing_profile_data = db_manager.get_user_memory(user_id)
        existing_profile = existing_profile_data['current_memory_profile'] if existing_profile_data else ""
        
        # Process the memory using AI
        updated_profile = process_user_memory(existing_profile, new_memory)
        
        # Save to database
        success = db_manager.set_user_memory(user_id, updated_profile, new_memory)
        
        if success:
            # Create embed for success response
            embed = discord.Embed(
                title="✅ Research Preferences Updated",
                description="Your research interests have been successfully updated and will be used to personalize arXiv paper summaries.",
                color=0x00ff00
            )
            
            # Show the updated profile (truncated if too long)
            profile_preview = updated_profile
            if len(profile_preview) > 800:
                profile_preview = profile_preview[:800] + "..."
            
            embed.add_field(
                name="📚 Your Current Research Profile",
                value=profile_preview,
                inline=False
            )
            
            embed.add_field(
                name="💡 How This Works",
                value="When you request arXiv papers, I'll now add a personalized \"Why You Should Read This\" section if the paper matches your interests.",
                inline=False
            )
            
            embed.set_footer(text="Use !mem --show to view your full profile • !mem --clear to reset")
            
            await processing_msg.edit(content="", embed=embed)
        else:
            await processing_msg.edit(content="❌ Failed to update your research preferences. Please try again.")
            
    except Exception as e:
        await message.channel.send(f"❌ An error occurred while processing your memory: {str(e)}")

async def show_user_memory(message, db_manager: DatabaseManager, user_id: str):
    """Show the user's current memory profile."""
    try:
        profile_data = db_manager.get_user_memory(user_id)
        
        if not profile_data:
            embed = discord.Embed(
                title="🧠 Your Research Profile",
                description="You don't have any research preferences stored yet.",
                color=0xffaa00
            )
            embed.add_field(
                name="💡 Get Started",
                value="Use `!mem <your research interests>` to set your preferences!\n\nExample: `!mem I'm interested in machine learning, natural language processing, and transformer architectures`",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="🧠 Your Research Profile",
                description="Here are your current research preferences:",
                color=0x0099ff
            )
            
            embed.add_field(
                name="📚 Current Profile",
                value=profile_data['current_memory_profile'],
                inline=False
            )
            
            # Show recent memory additions
            raw_memories = profile_data.get('raw_memories', [])
            if raw_memories:
                recent_memories = raw_memories[-3:]  # Last 3 memories
                memory_text = "\n".join([f"• {mem.get('memory', '')[:100]}{'...' if len(mem.get('memory', '')) > 100 else ''}" for mem in recent_memories])
                embed.add_field(
                    name="📝 Recent Additions",
                    value=memory_text,
                    inline=False
                )
            
            embed.add_field(
                name="📊 Profile Stats",
                value=f"Created: {profile_data['created_at']}\nLast Updated: {profile_data['updated_at']}\nTotal Memories: {len(raw_memories)}",
                inline=True
            )
            
            embed.set_footer(text="Use !mem <new interest> to add more • !mem --clear to reset")
        
        await message.channel.send(embed=embed)
        
    except Exception as e:
        await message.channel.send(f"❌ An error occurred while retrieving your memory: {str(e)}")

async def clear_user_memory(message, db_manager: DatabaseManager, user_id: str):
    """Clear the user's memory profile."""
    try:
        # Check if user has a profile first
        profile_data = db_manager.get_user_memory(user_id)
        
        if not profile_data:
            await message.channel.send("🤔 You don't have any research preferences stored to clear.")
            return
        
        # Clear the profile
        success = db_manager.clear_user_memory(user_id)
        
        if success:
            embed = discord.Embed(
                title="🗑️ Research Profile Cleared",
                description="Your research preferences have been successfully cleared.",
                color=0xff6b6b
            )
            embed.add_field(
                name="💡 Start Fresh",
                value="Use `!mem <your research interests>` to set new preferences whenever you're ready.",
                inline=False
            )
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("❌ Failed to clear your research preferences. Please try again.")
            
    except Exception as e:
        await message.channel.send(f"❌ An error occurred while clearing your memory: {str(e)}")

async def send_mem_help(message):
    """Send help information for the !mem command."""
    embed = discord.Embed(
        title="🧠 Memory Command Help",
        description="Store your research preferences to get personalized arXiv paper recommendations!",
        color=0x9966ff
    )
    
    embed.add_field(
        name="📝 Usage",
        value="`!mem <research interests>` - Add or update your research preferences\n`!mem --show` - View your current profile\n`!mem --clear` - Clear your profile",
        inline=False
    )
    
    embed.add_field(
        name="💡 Examples",
        value="`!mem I'm interested in deep learning and computer vision`\n`!mem I work on reinforcement learning for robotics`\n`!mem My research focuses on NLP and transformer models`",
        inline=False
    )
    
    embed.add_field(
        name="🎯 How It Works",
        value="After setting your preferences, when you request arXiv papers, I'll add a \"Why You Should Read This\" section if the paper matches your interests!",
        inline=False
    )
    
    await message.channel.send(embed=embed)
