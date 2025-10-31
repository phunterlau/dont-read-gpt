import re
import socket
import time
import json
import requests
from urllib.parse import urlparse

from url_processor import get_url_type_and_reader, generate_file_path
from content_processor import process_content
from indexer import Indexer
from database_manager import DatabaseManager
from utils.embed_builder import create_summary_embed, create_error_embed, create_processing_embed, create_existing_document_embed

async def handle_wget(message, indexer: Indexer, db_manager: DatabaseManager):
    """Handle !wget command or direct URL - retrieve and process content into both systems"""
    
    # Extract URL, potential focus, and force flag from the message
    parts = message.content.split(' ')
    command = parts[0]
    url = ""
    focus = None
    force_refresh = False
    use_arxiv_prompt = False

    if command == '!wget':
        # Parse wget command arguments
        args = parts[1:] if len(parts) > 1 else []
        
        # Check for --force flag (only supported for !wget command)
        if '--force' in args:
            force_refresh = True
            args.remove('--force')
        
        if args:
            url = args[0].strip()
            if len(args) > 1:
                focus = ' '.join(args[1:]).strip()
    else:
        # Direct URL posting - no --force flag support
        url = command.strip()
        if len(parts) > 1:
            focus = ' '.join(parts[1:]).strip()

    url, arxiv_id_detected = normalize_arxiv_identifier(url)
    if arxiv_id_detected:
        use_arxiv_prompt = True

    # Check if this is an arXiv URL for BOTH !wget command and direct URL
    if is_arxiv_url(url):
        use_arxiv_prompt = True

    # Basic URL validation
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
             # If no scheme, try adding https and re-parsing
            parsed_url = urlparse('https://' + url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                await message.channel.send(embed=create_error_embed("Invalid URL", "Please provide a valid URL.", command, url))
                return
    except ValueError:
        await message.channel.send(embed=create_error_embed("Invalid URL", "Could not parse the provided URL.", command, url))
        return

    start_time = time.time()
    
    # Send processing message using an embed
    if force_refresh:
        processing_embed = create_processing_embed(url)
        processing_embed.title = "🔄 Force Refreshing URL..."
        processing_embed.description = f"Force refreshing content from:\n{url}\n\n*Note: This will bypass cache and reprocess the document.*"
    else:
        processing_embed = create_processing_embed(url)
    
    processing_msg = await message.channel.send(embed=processing_embed)
    
    try:
        file_type, reader = get_url_type_and_reader(url)
        content = reader.read(url)
        
        file_path, time_now, complete_url = generate_file_path(url, file_type)
        
        # Check if document already exists (unless force refresh is requested)
        existing_doc = None
        if not force_refresh:
            existing_doc = db_manager.check_existing_document(complete_url)
        
        user_id = str(message.author.id)  # Get Discord user ID
        
        # Get user memory for personalization (only for arXiv papers)
        user_memory = None
        if use_arxiv_prompt:
            user_memory_data = db_manager.get_user_memory(user_id)
            if user_memory_data:
                user_memory = user_memory_data.get('current_memory_profile')
        
        if existing_doc and not force_refresh:
            # Check if document is outdated (older than 7 days)
            if db_manager.is_document_outdated(existing_doc['timestamp'], days_threshold=7):
                # Document is old, update it with new content
                summary_json, keywords = process_content(
                    file_type=file_type,
                    file_path=file_path,
                    timestamp=time_now,
                    content=content,
                    url=complete_url,
                    focus=focus,
                    use_arxiv_prompt=use_arxiv_prompt,
                    user_memory=user_memory
                )
                
                # Add to legacy indexer
                indexer.index_file(file_path)
                
                # Generate new embedding
                content_text = content
                if isinstance(content, dict):
                    content_text = content.get('content', str(content))
                
                from ai_func import generate_embedding
                embedding = generate_embedding(content_text) if content_text else []
                
                content_preview = content_text[:500] if isinstance(content_text, str) else str(content_text)[:500]
                
                # Update the existing document
                success = db_manager.update_document(
                    document_id=existing_doc['id'],
                    summary=summary_json,
                    keywords=keywords,
                    embedding=embedding,
                    content_preview=content_preview,
                    user_id=user_id
                )
                
                if success:
                    processing_time = time.time() - start_time
                    summary_embed = create_summary_embed(
                        summary_json=summary_json,
                        url=complete_url,
                        doc_type=file_type,
                        db_id=existing_doc['id'],
                        processing_time=processing_time,
                        is_updated=True
                    )
                    await processing_msg.edit(embed=summary_embed)
                else:
                    error_embed = create_error_embed("Database Error", "Failed to update existing document.", "!wget", url)
                    await processing_msg.edit(embed=error_embed)
                return
            else:
                # Document is recent, just display it
                # Check if we need to add personalization for this user
                summary_json = existing_doc['summary']
                
                if use_arxiv_prompt and user_memory:
                    # Add personalized section for cached arXiv documents
                    try:
                        from ai_func import generate_personalized_section
                        
                        # Generate personalized section
                        content_for_personalization = existing_doc.get('content_preview', '') or summary_json
                        personalized_text = generate_personalized_section(content_for_personalization, user_memory)
                        
                        if personalized_text:
                            # Parse existing summary and add personalized section
                            try:
                                summary_data = json.loads(summary_json)
                                summary_data['why_you_should_read'] = personalized_text
                                summary_json = json.dumps(summary_data)
                            except (json.JSONDecodeError, TypeError):
                                # If parsing fails, use original summary
                                pass
                    except Exception:
                        # If personalization fails, continue with original summary
                        pass
                
                # Create the document dict with potentially personalized summary
                doc_with_summary = existing_doc.copy()
                doc_with_summary['summary'] = summary_json
                
                existing_embed = create_existing_document_embed(doc_with_summary, existing_doc['id'])
                await processing_msg.edit(embed=existing_embed)
                return
        
        # Document doesn't exist OR force refresh is requested - create new one or update existing
        if force_refresh and existing_doc:
            # Force refresh: update existing document
            summary_json, keywords = process_content(
                file_type=file_type,
                file_path=file_path,
                timestamp=time_now,
                content=content,
                url=complete_url,
                focus=focus,
                use_arxiv_prompt=use_arxiv_prompt,
                user_memory=user_memory
            )
            
            # Add to legacy indexer
            indexer.index_file(file_path)
            
            # Generate new embedding
            content_text = content
            if isinstance(content, dict):
                content_text = content.get('content', str(content))
            
            from ai_func import generate_embedding
            embedding = generate_embedding(content_text) if content_text else []
            
            content_preview = content_text[:500] if isinstance(content_text, str) else str(content_text)[:500]
            
            # Update the existing document
            success = db_manager.update_document(
                document_id=existing_doc['id'],
                summary=summary_json,
                keywords=keywords,
                embedding=embedding,
                content_preview=content_preview,
                user_id=user_id
            )
            
            if success:
                processing_time = time.time() - start_time
                summary_embed = create_summary_embed(
                    summary_json=summary_json,
                    url=complete_url,
                    doc_type=file_type,
                    db_id=existing_doc['id'],
                    processing_time=processing_time,
                    is_updated=True
                )
                await processing_msg.edit(embed=summary_embed)
            else:
                error_embed = create_error_embed("Database Error", "Failed to force update existing document.", "!wget", url)
                await processing_msg.edit(embed=error_embed)
            return
        
        # Document doesn't exist, create new one
        summary_json, keywords = process_content(
            file_type=file_type,
            file_path=file_path,
            timestamp=time_now,
            content=content,
            url=complete_url,
            focus=focus,
            use_arxiv_prompt=use_arxiv_prompt,
            user_memory=user_memory
        )
        
        # Add to legacy indexer
        indexer.index_file(file_path)
        
        # Add to database
        content_text = content
        if isinstance(content, dict):
            content_text = content.get('content', str(content))
        
        from ai_func import generate_embedding
        embedding = generate_embedding(content_text) if content_text else []
        
        content_preview = content_text[:500] if isinstance(content_text, str) else str(content_text)[:500]
        
        doc_id = db_manager.add_document(
            url=complete_url,
            doc_type=file_type,
            timestamp=time_now,
            summary=summary_json,  # Store the JSON string directly
            file_path=file_path,
            keywords=keywords,
            embedding=embedding,
            content_preview=content_preview,
            user_id=user_id
        )
        
        processing_time = time.time() - start_time
        
        # Create the final summary embed
        summary_embed = create_summary_embed(
            summary_json=summary_json,
            url=complete_url,
            doc_type=file_type,
            db_id=doc_id,
            processing_time=processing_time,
            is_updated=False
        )
        
        await processing_msg.edit(embed=summary_embed)

    except (socket.gaierror, requests.exceptions.RequestException) as e:
        error_embed = create_error_embed("Network Error", str(e), "!wget", url)
        await processing_msg.edit(embed=error_embed)
        print(f'Network error for URL "{url}": {str(e)}')
    except Exception as e:
        # Catch JSON parsing errors from the summary as well
        error_message = str(e)
        if isinstance(e, json.JSONDecodeError):
            error_message = "Failed to parse AI summary response."
        
        error_embed = create_error_embed("Processing Error", error_message, "!wget", url)
        await processing_msg.edit(embed=error_embed)
        import traceback
        print(f'An error occurred while processing {url}: {e}')
        traceback.print_exc()

def normalize_arxiv_identifier(candidate: str):
    """Return normalized arXiv URL when the input is a bare identifier."""
    if not candidate:
        return candidate, False

    candidate = candidate.strip()
    match = re.fullmatch(r'(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)', candidate, flags=re.IGNORECASE)
    if not match:
        return candidate, False

    arxiv_id = match.group(1)
    normalized_url = f"https://arxiv.org/abs/{arxiv_id}"
    return normalized_url, True

def is_arxiv_url(url):
    """Check if the URL is an arXiv paper URL"""
    if not url:
        return False
    
    # Common arXiv URL patterns
    arxiv_patterns = [
        r'arxiv\.org',
        r'export\.arxiv\.org'
    ]
    
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in arxiv_patterns)
