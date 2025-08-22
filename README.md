# Discord Knowledge Bot

A Discord bot that processes URLs, extracts content, generates AI-powered summaries, and provides personalized research assistance with comprehensive search functionality.

## 🌟 Features

### Core Functionality
- **URL Processing**: Automatically process URLs from ArXiv, GitHub, YouTube, Hugging Face, Reddit, and general web pages
- **AI-Powered Summaries**: Generate intelligent summaries using GPT-4o with keyword extraction
- **Personalized Research**: Store user research interests for personalized arXiv paper recommendations
- **Dual Storage System**: Both SQLite database and legacy CSV indexing for reliability
- **Multi-User Support**: Complete user isolation with personalized document libraries
- **Rich Discord Integration**: Beautiful embeds with progress indicators and error handling

### Supported Content Sources
- **ArXiv Papers**: Enhanced processing with personalized "Why You Should Read This" sections
- **PDF Documents**: Direct PDF text extraction and processing from any URL
- **GitHub Repositories**: README and code analysis
- **YouTube Videos**: Transcript extraction and summarization
- **Hugging Face Models**: Model card analysis
- **Reddit Threads**: Thread summarization
- **General Web Pages**: Content extraction and analysis

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/phunterlau/dont-read-gpt
cd dont-read-gpt

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_KEY=your_openai_api_key
export DISCORD_TOKEN=your_discord_bot_token
export REDDIT_APP_ID=your_reddit_app_id      # Optional
export REDDIT_APP_SECRET=your_reddit_app_secret  # Optional

# Run the bot
python my_bot.py
```

### Basic Usage
```discord
# Process a URL (automatic detection)
https://arxiv.org/abs/2304.14979

# Or use explicit command
!wget https://arxiv.org/abs/2304.14979

# Force refresh a document (bypasses cache, reprocesses content)
!wget --force https://arxiv.org/abs/2304.14979

# Search arXiv for papers and auto-process the top result
!find transformer architectures
!find machine learning optimization

# Set your research interests for personalized arXiv summaries
!mem I'm interested in transformer architectures and attention mechanisms

# Search your documents
!grep machine learning
!egrep "neural networks"

# View statistics
!stats

# See recent additions
!tail
```

## 📋 Commands Reference

### 🔍 Search Commands
- `!grep <query>` - Search all content and summaries (case-insensitive)
- `!egrep <keyword>` - Search by keyword (case-insensitive)
- `!related <id>` - Find documents related to a specific document
- `!find <keywords>` - Search arXiv for papers matching keywords, auto-process the top result

### 📥 Content Management
- `!wget <url>` - Process a URL explicitly
- `!wget --force <url>` - Force refresh and reprocess a URL (bypasses cache)
- Direct URL posting - Just paste a URL for automatic processing

### 🧠 Personalization (NEW!)
- `!mem <interests>` - Set your research interests for personalized arXiv summaries
- `!mem --show` - View your current research profile
- `!mem --clear` - Clear your research profile

### 📊 Information & Utilities
- `!stats` - Show system statistics (documents, keywords, usage)
- `!tail` - Show 3 most recently processed documents
- `!whoami` - Show your Discord user information
- `!index` - Reindex documents (admin)
- `!migrate` - Database migration utilities (admin)

## 🏗️ Project Structure

### Entry Point
```
my_bot.py                 # Main Discord bot entry point
```

### Core Systems
```
database_manager.py       # SQLite database operations
indexer.py               # Legacy CSV indexing system
ai_func.py               # GPT integration and AI functions
content_processor.py     # Content processing pipeline
url_processor.py         # URL routing and reader selection
```

### Command Handlers
```
commands/
├── mem_handler.py           # Personalized memory system
├── wget_handler.py          # URL processing
├── find_handler.py          # arXiv search and processing
├── search_handler.py        # Text search (!grep)
├── keyword_search_handler.py # Keyword search (!egrep)
├── stats_handler.py         # Statistics
├── tail_handler.py          # Recent documents
├── related_handler.py       # Related documents
├── index_handler.py         # Indexing
├── migrate_handler.py       # Migration
└── whoami_handler.py        # User info
```

### Content Readers
```
readers/
├── base_reader.py           # Abstract base class
├── arxiv_reader.py          # ArXiv paper processing
├── pdf_reader.py            # Direct PDF document processing
├── github_reader.py         # GitHub repository analysis
├── youtube_reader.py        # YouTube transcript extraction
├── huggingface_reader.py    # Hugging Face model cards
├── reddit_reader.py         # Reddit thread processing
└── webpage_reader.py        # General web page content
```

### Utilities
```
utils/
└── embed_builder.py         # Discord embed generation

tools/
├── migrate_to_database.py   # CSV to SQLite migration
└── db_helper.py             # Database maintenance utilities
```

## 🗄️ Database Schema

### Documents Table
```sql
documents (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    type TEXT,                    -- 'arxiv', 'github', 'youtube', etc.
    timestamp REAL,
    summary TEXT,                 -- AI-generated summary
    file_path TEXT,              -- Path to JSON file
    content_preview TEXT,        -- First 500 chars of content
    user_id TEXT,                -- User isolation
    updated_at REAL             -- Last update timestamp
)
```

### Keywords Table
```sql
keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL,
    document_id INTEGER,
    user_id TEXT,                -- User isolation
    FOREIGN KEY (document_id) REFERENCES documents (id)
)
```

### User Profiles Table (NEW!)
```sql
user_profiles (
    user_id TEXT PRIMARY KEY,
    current_memory_profile TEXT NOT NULL,  -- AI-processed research interests
    raw_memories TEXT,                     -- JSON array of raw inputs
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### Embeddings Table (Future Use)
```sql
embeddings (
    document_id INTEGER PRIMARY KEY,
    embedding BLOB,              -- Vector embeddings for similarity search
    FOREIGN KEY (document_id) REFERENCES documents (id)
)
```

## 🤖 AI Integration

### Memory Processing
- **User Research Profiles**: Store and synthesize research interests using GPT-4o-mini
- **Personalized Summaries**: Generate "Why You Should Read This" sections for arXiv papers
- **Context-Aware Processing**: Different summarization strategies for different content types

### Summary Generation
- **ArXiv Papers**: Enhanced academic summaries with technical depth
- **Code Repositories**: Focus on functionality and technical implementation
- **General Content**: Balanced summaries with key insights

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_KEY=sk-...                    # Required: OpenAI API key
DISCORD_TOKEN=your_discord_token     # Required: Discord bot token
REDDIT_APP_ID=your_reddit_id         # Optional: Reddit API access
REDDIT_APP_SECRET=your_reddit_secret # Optional: Reddit API access
```

### Bot Configuration
```python
# In my_bot.py
AUTO_MIGRATE_EXISTING_DATA = False   # Set to True for automatic CSV migration
```

## 🎯 Key Features in Detail

### ArXiv Paper Discovery with !find

The `!find` command provides intelligent arXiv paper discovery:

1. **Natural Language Search**: `!find transformer architectures` - No quotes needed
2. **Relevance Ranking**: Uses arXiv API to find the most relevant paper based on abstracts
3. **Automatic Processing**: Downloads and processes the top result through the full pipeline
4. **Robust URL Handling**: Handles all arXiv URL formats including versioned URLs (v1, v2, etc.)
5. **Duplicate Prevention**: Checks if paper already exists in your library
6. **Full Integration**: Leverages existing wget pipeline, AI summarization, and personalization

**Example Usage:**

```discord
!find transformer architectures
!find machine learning optimization
!find neural network pruning techniques
!find deep reinforcement learning survey
```

### PDF Document Processing

The bot automatically detects and processes PDF documents from direct URLs:

1. **Automatic Detection**: Any URL ending in `.pdf` or serving PDF content
2. **Text Extraction**: Uses pdfplumber to extract readable text from PDF files
3. **Full Pipeline Integration**: PDFs get the same AI summarization and keyword extraction
4. **File Storage**: Saves both the extracted text (JSON) and original PDF file
5. **Content Cleaning**: Removes PDF artifacts and formats text for better readability

**Example Usage:**

```discord
# Direct PDF URL processing
https://example.com/document.pdf
!wget https://dennyzhou.github.io/LLM-Reasoning-Stanford-CS-25.pdf

# Works with academic papers, reports, presentations, etc.
```

**Supported PDF Sources:**
- Academic papers from university websites
- Research reports and whitepapers
- Technical documentation
- Conference presentations
- Any publicly accessible PDF document

### Personalized Research Assistant

The `!mem` command creates a personalized research experience:

1. **Store Interests**: `!mem I study transformer architectures and attention mechanisms`
2. **Get Recommendations**: ArXiv papers automatically include personalized relevance explanations
3. **Privacy**: Each user's profile is completely isolated

### Dual Storage Reliability
- **SQLite Database**: Primary storage with full relational capabilities
- **Legacy CSV System**: Backup storage ensuring no data loss during transitions
- **Automatic Sync**: Both systems stay synchronized for reliability

### Multi-User Support
- **Complete Isolation**: Users only see their own documents and searches
- **User-Specific Stats**: Personal document counts and keyword analytics
- **Shared Knowledge**: Option to discover public documents (future feature)

## 🧪 Testing

The project includes comprehensive test suites:
```bash
# Core functionality tests
python tests/test_phase1.py
python tests/test_phase2.py
python tests/test_phase3.py

# Memory system tests
python test_mem_phase1.py
python test_mem_phase2.py
python test_mem_phase3.py
python test_mem_integration.py
```

## 🚀 Future Enhancements

### Planned Features
- **Vector Search**: Semantic similarity using embeddings
- **Advanced Analytics**: Research trend analysis and insights
- **Export Functions**: Save collections to files or Obsidian vaults
- **Collaboration Features**: Share documents and create team collections

### API Ready
The modular architecture makes it easy to:
- Add new content sources
- Implement additional AI features
- Create web interfaces
- Build mobile applications

## 📄 Documentation

- [`how-to-en.md`](how-to-en.md) - Comprehensive English user guide
- [`how-to-zh-cn.md`](how-to-zh-cn.md) - Chinese user documentation
- [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [`UPDATED_COMMANDS_REFERENCE.md`](UPDATED_COMMANDS_REFERENCE.md) - Complete command reference

## 🤝 Contributing

The bot is designed for easy extension:
1. **New Content Sources**: Inherit from `BaseReader` class
2. **New Commands**: Add handler to `commands/` directory
3. **Database Changes**: Update `database_manager.py` schema
4. **AI Features**: Extend `ai_func.py` with new capabilities

---

**Built with Python, Discord.py, SQLite, and OpenAI GPT-4o for intelligent research assistance.**