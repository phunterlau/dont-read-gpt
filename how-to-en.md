# Discord Knowledge Bot User Guide

## 🤖 Bot Introduction

This is a powerful Discord knowledge management bot that automatically processes web links, extracts content, generates summaries, and provides intelligent search functionality. The bot supports multiple content sources including ArXiv papers, GitHub repositories, YouTube videos, and more.

## 📋 Available Commands

### 🔍 Search Commands

#### `!grep <search_term>`
**Function:** Full-text search across document content and summaries  
**Description:** Case-insensitive text search through all indexed content  
**Examples:**
```
!grep machine learning
!grep "neural networks"
!grep ChatGPT
!grep artificial intelligence
```
**Search results include:** Document title, URL, timestamp, keywords, summary excerpts

---

#### `!egrep <keyword>`
**Function:** Keyword search  
**Description:** Search within extracted keywords with fuzzy matching support  
**Examples:**
```
!egrep ChatGPT
!egrep "Large Language Models"
!egrep "deep learning"
!egrep AutoML
```
**Features:** Highlights matching keywords and displays related document metadata

---

### 📥 Content Processing Commands

#### `!wget <url>` or Direct URL
**Function:** Download and process web content  
**Description:** Automatically detects content type, generates AI summaries, extracts keywords, and saves to database  
**Examples:**
```
!wget https://arxiv.org/abs/2304.14979
!wget https://github.com/microsoft/vscode
!wget https://www.youtube.com/watch?v=xyz123
```

**Direct URL submission:**
```
https://arxiv.org/abs/2304.14979
https://news.ycombinator.com/item?id=123456
https://huggingface.co/microsoft/DialoGPT-medium
```

**Supported website types:**
- 📄 ArXiv academic papers (special academic analysis)
- 💻 GitHub repositories and notebooks
- 🎥 YouTube videos (transcript extraction)
- 🤗 Hugging Face model pages
- 📱 WeChat articles
- 🌐 General web pages

**Special features:**
- ArXiv papers use specialized academic analysis prompts
- Automatically generates Obsidian-compatible markdown format
- Creates keyword internal links

---

### 📊 Information Query Commands

#### `!stats`
**Function:** Display database statistics  
**Description:** Shows document counts, keyword statistics, document type distribution, etc.  
**Example:**
```
!stats
```

**Display content:**
- Total document count (legacy + database systems combined)
- Keyword count statistics
- Document type distribution (arxiv, github, youtube, etc.)
- Popular keywords
- Recently added documents
- Database size information

---

#### `!tail`
**Function:** Display the 3 most recently added documents  
**Description:** Quick view of the latest processed content  
**Example:**
```
!tail
```

**Display information:**
- URLs of the 3 most recent documents
- Addition timestamps
- Document types
- Source system identifiers

---

### 🔧 Management Commands

#### `!related <document_id>`
**Function:** Find related documents  
**Description:** Finds documents based on shared keywords  
**Examples:**
```
!related 123
!related 456
```

**How it works:** Analyzes keywords of the specified document to find other documents with similar keywords

---

#### `!index`
**Function:** Reindex documents (legacy system)  
**Description:** Rebuilds the search index for the legacy system  
**Example:**
```
!index
```

**Note:** Primarily used for maintaining the legacy CSV index system

---

#### `!migrate`
**Function:** Data migration  
**Description:** Migrates legacy CSV data to the new SQLite database  
**Example:**
```
!migrate
```

**Purpose:** Data migration tool for system upgrades

---

#### `!mem <research interests>` or `!mem --show` or `!mem --clear`
**Function:** Store research preferences for personalized arXiv summaries  
**Description:** Store your research interests to get personalized "Why You Should Read This" sections for arXiv papers  

**Setting your preferences:**
```
!mem I'm interested in machine learning and neural networks
!mem I work on transformer architectures and NLP
!mem My research focuses on computer vision and deep learning
```

**Viewing your profile:**
```
!mem --show
```

**Clearing your profile:**
```
!mem --clear
```

**How personalization works:**
- After setting preferences, arXiv papers will include a personalized "🤔 Why You Should Read This" section
- The bot analyzes if the paper matches your interests and explains why it's relevant
- Personalization is user-specific and doesn't affect cached summaries for other users
- Non-arXiv content is not personalized
- The AI only adds the section if the paper is genuinely relevant to your interests

**Example workflow:**
1. `!mem I'm interested in transformer architectures and attention mechanisms`
2. `https://arxiv.org/abs/1706.03762` (send an Attention Is All You Need paper URL)
3. You'll see a personalized section explaining why this paper is relevant to your research interests!

---

#### `!whoami`
**Function:** Show current user information  
**Description:** Displays your Discord user ID, username, and document count  
**Example:**
```
!whoami
```

**Shows:**
- Username and display name
- Discord user ID
- Account creation date
- Number of documents you've added to the database
- User avatar (if available)

---

## 🎯 Usage Tips

### 💡 Search Tips
1. **Use quotes:** Search exact phrases `!grep "machine learning"`
2. **Keyword search:** Use `!egrep` to search extracted keywords
3. **URL filtering:** Include domain names in search terms to filter specific sites

### 🔗 URL Processing Tips
1. **Direct paste:** Send URL links directly without the `!wget` command
2. **Batch processing:** Send multiple links consecutively
3. **ArXiv optimization:** ArXiv papers automatically use academic analysis mode

### 📚 Content Organization
1. **Keyword associations:** System automatically extracts keywords to establish document relationships
2. **Time series:** Use `!tail` to view recent activity
3. **Related discovery:** Use `!related` to discover related content

## 🚀 Quick Start

### First Time Usage
1. Try sending a URL:
   ```
   https://arxiv.org/abs/2304.08424
   ```

2. Check statistics:
   ```
   !stats
   ```

3. Search for interesting content:
   ```
   !grep artificial intelligence
   ```

### Common Workflow
1. **Content collection:** Send URLs or use `!wget`
2. **Search and find:** Use `!grep` or `!egrep` to find relevant content
3. **Relationship exploration:** Use `!related` to discover related documents
4. **Regular review:** Use `!tail` to check recently collected content

## ⚠️ Important Notes

- All searches are case-insensitive
- Search results are limited to top 5 to avoid information overload
- Long URLs are automatically truncated for display
- System maintains both new and legacy indexes for compatibility
- ArXiv papers receive specialized academic analysis
- Generated content includes Obsidian-compatible internal link formatting

## 🎨 Response Format

Bot replies use structured formatting:
- 📅 Timestamp
- 🏷️ Document type tags  
- 🔑 Keyword list
- 📝 Content summary
- 🔗 Original link

This format enables quick browsing and understanding of content highlights.

---

**Tip:** Try out different commands to familiarize yourself with the bot's features!
