from indexer import Indexer

async def handle_related(message, indexer: Indexer, db_manager):
    """Handle !related command - find user's documents related to a given document"""
    
    if len(message.content.split(' ')) < 2:
        await message.channel.send('Usage: !related <document_id>\n*Note: Only your documents are searched*')
        return
    
    user_id = str(message.author.id)  # Get user ID for filtering
    
    try:
        document_id = int(message.content.split(' ', 1)[1].strip())
    except ValueError:
        await message.channel.send('Document ID must be a number')
        return
    
    # First check if document exists and belongs to user (for new DB documents)
    db_doc = db_manager.get_document_by_id(document_id, user_id=user_id)
    
    # For legacy documents, use the indexer (no user filtering yet)
    legacy_doc = indexer.get_document_by_id(document_id)
    
    document = db_doc or legacy_doc
    
    if not document:
        await message.channel.send(f'Document not found with ID: {document_id} in your collection\n*Note: You can only view your own documents*')
        return
    
    # Get related documents (prefer DB if available, fallback to legacy)
    if db_doc:
        # Use semantic search on user's documents for better results
        query = document.get('summary', document.get('url', ''))[:100]  # Use summary as query
        related_results = db_manager.semantic_search(query, limit=5, user_id=user_id)
        # Filter out the original document
        related = [r for r in related_results if r.get('id') != document_id]
    else:
        # Legacy system - no user filtering available yet
        related = indexer.get_related_documents(document_id)
    
    if not related:
        await message.channel.send(f'No related documents found in your collection for ID: {document_id}')
        return
    
    # Get the document's keywords
    document_keywords = document.get('keywords', [])
    if isinstance(document_keywords, str):
        document_keywords = [k.strip() for k in document_keywords.split(',')]
    
    # Start with basic info
    response_parts = [
        f'**Your related documents for [{document["url"]}]:**',
        f'**Keywords:** {", ".join(document_keywords) if document_keywords else "None"}',
        f'*Note: Only your documents are searched*',
        ''
    ]
    
    # Add each related document
    for i, result in enumerate(related, 1):
        if i > 5:  # Limit to top 5
            break
            
        # Handle both DB and legacy document formats
        if isinstance(result, dict) and 'similarity' in result:
            # DB document with similarity score
            doc_info = [
                f"{i}. [{result['url']}]",
                f"   Relevance: {result.get('similarity', 0):.1%}",
                f"   Summary: {result.get('summary', 'No summary')[:200]}{'...' if len(result.get('summary', '')) > 200 else ''}",
                ''
            ]
        else:
            # Legacy document format
            related_doc = indexer.get_document_by_id(result['id']) if 'id' in result else result
            related_keywords = related_doc.get('keywords', [])
            if isinstance(related_keywords, str):
                related_keywords = [k.strip() for k in related_keywords.split(',')]
            
            # Find shared keywords
            shared_keywords = [k for k in related_keywords if k in document_keywords]
            
            doc_info = [
                f"{i}. [{result['url']}]",
                f"   Type: {result.get('type', 'unknown')}, Shared keywords: {', '.join(shared_keywords) if shared_keywords else 'None'}",
                f"   Summary: {result.get('summary', 'No summary')[:200]}{'...' if len(result.get('summary', '')) > 200 else ''}",
                ''
            ]
        
        # Check if adding this document would exceed Discord's limit
        test_response = '\n'.join(response_parts + doc_info)
        if len(test_response) > 1900:  # Leave some buffer
            # Send what we have so far
            await message.channel.send('\n'.join(response_parts))
            
            # Start a new message with remaining documents
            response_parts = [f"**(continued - your related documents {i}-{len(related)}):**", '']
            
        response_parts.extend(doc_info)
    
    # Send the final message
    if response_parts:
        final_message = '\n'.join(response_parts)
        if len(final_message) > 2000:
            # Split into chunks if still too long
            chunks = final_message.split('\n\n')
            current_chunk = []
            current_length = 0
            
            for chunk in chunks:
                if current_length + len(chunk) + 2 > 1900:  # +2 for \n\n
                    if current_chunk:
                        await message.channel.send('\n\n'.join(current_chunk))
                    current_chunk = [chunk]
                    current_length = len(chunk)
                else:
                    current_chunk.append(chunk)
                    current_length += len(chunk) + 2
            
            if current_chunk:
                await message.channel.send('\n\n'.join(current_chunk))
        else:
            await message.channel.send(final_message)
    return
