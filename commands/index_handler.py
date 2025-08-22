import os
from indexer import Indexer

async def handle_index(message, indexer: Indexer):
    if message.content.strip() == '!index':
        # Index all files
        await message.channel.send('Indexing all files...')
        total, indexed = indexer.index_all_files()
        await message.channel.send(f'Indexed {indexed} out of {total} files')
        
        # Get and display stats
        stats = indexer.get_stats()
        stats_message = f"**Indexing Stats:**\n"
        stats_message += f"Total documents: {stats['total_documents']}\n"
        stats_message += f"Documents by type: {', '.join([f'{k}: {v}' for k, v in stats['documents_by_type'].items()])}\n"
        stats_message += f"Total keywords: {stats['total_keywords']}\n"
        stats_message += f"Unique keywords: {stats['unique_keywords']}\n"
        stats_message += f"Top keywords: {', '.join([f'{k}: {v}' for k, v in stats['top_keywords'].items()])[:1000]}\n"
        await message.channel.send(stats_message[:2000])  # Discord message limit
        return
    else:
        # Index a specific file or directory
        path = message.content.split(' ', 1)[1].strip()
        if os.path.isfile(path):
            success = indexer.index_file(path)
            await message.channel.send(f'File {"indexed successfully" if success else "indexing failed"}: {path}')
        elif os.path.isdir(path):
            total, indexed = indexer.index_all_files(path)
            await message.channel.send(f'Indexed {indexed} out of {total} files in {path}')
        else:
            await message.channel.send(f'Path not found: {path}')
        return
