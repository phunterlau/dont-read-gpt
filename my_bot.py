import discord
import os
from indexer import Indexer
from database_manager import DatabaseManager

from commands.index_handler import handle_index
from commands.search_handler import handle_search
from commands.keyword_search_handler import handle_keyword_search
from commands.related_handler import handle_related
from commands.stats_handler import handle_stats
from commands.wget_handler import handle_wget
from commands.tail_handler import handle_tail
from commands.migrate_handler import handle_migrate
from commands.whoami_handler import handle_whoami
from commands.mem_handler import handle_mem

# Initialize Discord client
intents = discord.Intents.default()
intents.members = True
discord_token = os.environ['DISCORD_TOKEN']
client = discord.Client(intents=intents)

# Configuration options
AUTO_MIGRATE_EXISTING_DATA = False  # Set to True to automatically migrate CSV data to database on startup

# Initialize the indexer and database manager
indexer = Indexer(auto_migrate=AUTO_MIGRATE_EXISTING_DATA)
db_manager = DatabaseManager()

# Command dispatcher
COMMANDS = {
    '!index': handle_index,
    '!grep': handle_search,
    '!egrep': handle_keyword_search,
    '!related': handle_related,
    '!stats': handle_stats,
    '!wget': handle_wget,
    '!tail': handle_tail,
    '!migrate': handle_migrate,
    '!whoami': handle_whoami,
    '!mem': handle_mem,
}

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    print('Indexer initialized')
    print('Database manager initialized')
    print(f'Auto-migration of existing data: {"ENABLED" if AUTO_MIGRATE_EXISTING_DATA else "DISABLED"}')
    if not AUTO_MIGRATE_EXISTING_DATA:
        print('To enable auto-migration, set AUTO_MIGRATE_EXISTING_DATA = True in my_bot.py')
        print('Or run: python tools/migrate_to_database.py')
    print('Available commands: !grep, !egrep, !stats, !wget, !tail, !index, !related, !migrate, !whoami, !mem')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    command = message.content.split(' ')[0]

    if command in COMMANDS:
        if command in ['!index', '!grep', '!egrep', '!related', '!stats', '!wget', '!tail', '!migrate', '!whoami', '!mem']:
            await COMMANDS[command](message, indexer, db_manager)
        else:
            await COMMANDS[command](message)
    # Also treat messages that are just a URL as a !wget command
    elif message.content.startswith('http://') or message.content.startswith('https://') or message.content.startswith('www.'):
        await handle_wget(message, indexer, db_manager)


if __name__ == '__main__':
    try:
        client.run(discord_token)
    finally:
        # Close the indexer and database connections when the bot shuts down
        indexer.close()
        db_manager.close()

