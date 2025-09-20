import discord
import arxiv
import re
from commands.wget_handler import handle_wget

# ---- Helper Functions for Title-only Search ----

def _normalize_title(text: str) -> str:
    text = text.lower()
    # Remove punctuation except alphanumerics and spaces
    text = re.sub(r'[^0-9a-z\s]+', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _tokenize(text: str):
    return _normalize_title(text).split()

def _jaccard(a_tokens, b_tokens):
    a, b = set(a_tokens), set(b_tokens)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def _sequence_overlap(a_tokens, b_tokens):
    # Simple longest common subsequence length approximation using dynamic programming (capped for efficiency)
    a, b = a_tokens, b_tokens
    if not a or not b:
        return 0.0
    # Cap lengths to avoid large DP (titles are short so fine)
    dp = [[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    lcs = dp[len(a)][len(b)]
    return lcs / max(len(a), len(b))

def _composite_score(query_title: str, candidate_title: str) -> float:
    q_norm = _normalize_title(query_title)
    c_norm = _normalize_title(candidate_title)
    if q_norm == c_norm:
        return 1.0
    q_tokens = q_norm.split()
    c_tokens = c_norm.split()
    j = _jaccard(q_tokens, c_tokens)
    seq = _sequence_overlap(q_tokens, c_tokens)
    # Weighted combination – tweakable
    score = 0.6 * j + 0.4 * seq
    # Light bonus for prefix alignment
    if ' '.join(q_tokens[:3]) == ' '.join(c_tokens[:3]):
        score += 0.05
    return min(score, 0.999)

def _title_field_query_exact(original: str) -> str:
    # Use double quotes to enforce phrase search in title field
    return f'ti:"{original}"'

def _title_field_query_normalized(original: str) -> str:
    return f'ti:"{_normalize_title(original)}"'

def _title_field_tokens_and(original: str) -> str:
    toks = _tokenize(original)
    # Take up to first 8 tokens to avoid over-long queries
    toks = toks[:8]
    return ' AND '.join([f'ti:{t}' for t in toks])

def _gather_candidates(client, queries, max_per_query=10):
    seen = {}
    for q in queries:
        if not q:
            continue
        try:
            search = arxiv.Search(query=q, max_results=max_per_query, sort_by=arxiv.SortCriterion.Relevance)
            for result in client.results(search):
                if result.entry_id not in seen:
                    seen[result.entry_id] = result
        except Exception:
            continue
    return list(seen.values())

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
        client = arxiv.Client()
        original_query = content

        # Build staged title-only queries
        queries = [
            _title_field_query_exact(original_query),
            _title_field_query_normalized(original_query),
            _title_field_tokens_and(original_query)
        ]

        candidates = _gather_candidates(client, queries, max_per_query=12)

        if not candidates:
            await search_msg.edit(content=f"❌ No arXiv papers found for title: **{content}**")
            return

        # Rerank by composite similarity to the original full title
        scored = []
        for c in candidates:
            score = _composite_score(original_query, c.title)
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)

        top_score, top_result = scored[0]

        # Threshold: if low confidence, inform user but still proceed
        low_conf = top_score < 0.55

        paper_url = top_result.entry_id
        paper_title = top_result.title
        paper_authors = ", ".join([str(author) for author in top_result.authors[:3]])
        if len(top_result.authors) > 3:
            paper_authors += " et al."

        # Normalize arXiv URL (strip version)
        clean_url = paper_url
        if 'arxiv.org' in paper_url:
            from readers.arxiv_reader import extract_arxiv_id
            arxiv_id = extract_arxiv_id(paper_url, include_version=False)
            if arxiv_id:
                clean_url = f"https://arxiv.org/abs/{arxiv_id}"

        # Optional: show top 3 alternative titles if best is not exact
        alt_lines = []
        for alt_score, alt in scored[1:4]:
            alt_lines.append(f"{alt_score:.2f} – {alt.title[:90]}" + ("…" if len(alt.title) > 90 else ""))
        alt_block = "\n".join(alt_lines) if alt_lines else ""

        confidence_note = "⚠️ Low confidence match based on title similarity.\n\n" if low_conf else ""

        await search_msg.edit(
            content=(f"{confidence_note}✅ **Selected paper (title-only search):**\n"
                     f"📄 **{paper_title}**\n"
                     f"👥 {paper_authors}\n"
                     f"🔗 {clean_url}\n"
                     f"🔍 Similarity score: {top_score:.2f}\n"
                     + (f"\nAlternative candidates:\n{alt_block}\n" if alt_block else "")
                     + "\n⚡ Processing paper...")
        )

        class MockMessage:
            def __init__(self, original_message, new_content):
                self.author = original_message.author
                self.channel = original_message.channel
                self.guild = original_message.guild
                self.id = original_message.id
                self.created_at = original_message.created_at
                self.content = new_content

        mock_message = MockMessage(message, clean_url)
        await handle_wget(mock_message, indexer, db_manager)

    except Exception as e:
        await search_msg.edit(
            content=f"❌ **Error searching arXiv:**\n"
                   f"```\n{str(e)}\n```\n"
                   f"Please try again or check your search terms."
        )
