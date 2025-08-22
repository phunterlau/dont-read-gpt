# Discord Knowledge Bot - Changelog

## Recent Updates (Since !mem Implementation)

### v2.3.0 - Force Refresh & PDF Support (August 22, 2025)

#### 🆕 New Features
- **PDF Document Processing**: Added support for direct PDF URL processing
  - Automatically detects PDF URLs by extension or content-type
  - Extracts text content using pdfplumber library
  - Full AI summarization and keyword extraction pipeline
  - Downloads and stores both JSON metadata and original PDF files

- **Force Refresh Functionality**: Added `--force` flag to `!wget` command
  - `!wget --force <url>` - Bypasses cache and reprocesses existing documents
  - Flexible flag positioning: works before or after URL
  - Scope-limited: only available for explicit `!wget` command, not direct URL posting
  - Visual feedback with "Force Refreshing" processing message

#### 🔧 Technical Improvements
- **New Reader**: `readers/pdf_reader.py` for PDF text extraction
- **Enhanced URL Processing**: Updated `url_processor.py` to detect and route PDF URLs
- **Content Pipeline**: Extended `content_processor.py` to handle PDF downloads
- **Command Parsing**: Improved argument parsing in `wget_handler.py` for flag support

#### 📚 Dependencies Added
- `pdfplumber==0.10.3` - PDF text extraction library

#### 📋 Usage Examples
```discord
# PDF Processing
https://example.com/document.pdf
!wget https://dennyzhou.github.io/LLM-Reasoning-Stanford-CS-25.pdf

# Force Refresh
!wget --force https://arxiv.org/abs/2304.14979
!wget https://example.com/paper.pdf --force
```

### v2.2.0 - ArXiv Discovery (Previous Update)

#### 🆕 New Features
- **ArXiv Paper Discovery**: Added `!find` command for intelligent paper search
  - Natural language search queries without quotes
  - Relevance-based ranking using arXiv API
  - Automatic processing of top search result
  - Full integration with existing wget pipeline and personalization

#### 🔧 Technical Improvements
- **New Handler**: `commands/find_handler.py` for arXiv search functionality
- **Enhanced ArXiv Support**: Improved URL handling for versioned arXiv URLs
- **Bug Fixes**: Resolved JSON variable conflicts and URL version number issues

#### 📚 Dependencies Added
- `arxiv==2.2.0` - ArXiv API integration

#### 📋 Usage Examples
```discord
!find transformer architectures
!find machine learning optimization
!find neural network pruning
```

### v2.1.0 - Personalization System (Base Implementation)

#### 🆕 Core Features
- **Memory System**: `!mem` command for personalized research interests
- **User Profiles**: SQLite database storage for user preferences
- **Personalized Summaries**: "Why You Should Read This" sections for arXiv papers
- **User Isolation**: Complete separation of user data and search results

---

## Feature Summary

| Feature | Command | Description |
|---------|---------|-------------|
| **Memory System** | `!mem <interests>` | Store research interests for personalization |
| **ArXiv Discovery** | `!find <keywords>` | Search and auto-process arXiv papers |
| **PDF Processing** | Direct URL / `!wget` | Extract and process PDF documents |
| **Force Refresh** | `!wget --force <url>` | Bypass cache and reprocess documents |
| **Search** | `!grep`, `!egrep` | Search through processed content |
| **Statistics** | `!stats`, `!tail` | View system usage and recent documents |

## Supported Content Types
- ✅ ArXiv Papers (with personalization)
- ✅ PDF Documents (direct URLs)
- ✅ GitHub Repositories
- ✅ Hugging Face Models
- ✅ Reddit Threads
- ✅ General Web Pages

## Next Planned Features
- Vector similarity search using embeddings
- Export functionality for collections
- Advanced analytics and research insights
- Multi-user collaboration features
