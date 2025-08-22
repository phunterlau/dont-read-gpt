from database_manager import DatabaseManager

async def handle_migrate(message, indexer, db_manager):
    """Handle !migrate command - manually trigger migration from CSV to database"""
    
    # Send initial message
    processing_msg = await message.channel.send('⏳ Starting migration from CSV to database...')
    
    try:
        import os
        csv_path = "saved_text/index.csv"
        
        if not os.path.exists(csv_path):
            await processing_msg.edit(content='❌ **Migration skipped:** No CSV index file found at `saved_text/index.csv`')
            return
        
        # Trigger migration
        print("Manual migration triggered from Discord...")
        db_manager.migrate_from_csv(csv_path, "saved_text")
        
        # Get updated stats
        stats = db_manager.get_stats()
        
        message_parts = [
            '✅ **Migration completed successfully!**',
            f'📊 **Database Statistics:**',
            f'   • Total documents: {stats["total_documents"]}',
            f'   • Total keywords: {stats["total_keywords"]}',
            f'   • Unique keywords: {stats["unique_keywords"]}',
            f'   • Documents by type: {", ".join([f"{k}:{v}" for k, v in stats["documents_by_type"].items()])}',
            '',
            '🔍 **Next steps:**',
            '   • Use `!stats` to see detailed statistics',
            '   • Use `!grep <term>` to search content',
            '   • Use `!egrep <keyword>` to search keywords'
        ]
        
        await processing_msg.edit(content='\n'.join(message_parts))
        print("Migration completed successfully from Discord command.")
        
    except Exception as e:
        error_msg = f'❌ **Migration failed:** {str(e)}'
        await processing_msg.edit(content=error_msg)
        print(f'Migration error: {e}')
