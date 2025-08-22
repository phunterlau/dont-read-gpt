from ai_func import generate_summary, generate_embedding
from readers.arxiv_reader import download_arxiv_pdf
from readers.pdf_reader import download_pdf
import json
import os

def process_content(file_type, file_path, timestamp, content, url, focus=None, use_arxiv_prompt=False, user_memory=None):
    """
    Processes the raw content to generate a structured summary and save all relevant data.
    """
    summary_json_str = generate_summary(content, summary_type=file_type, focus=focus, use_arxiv_prompt=use_arxiv_prompt, user_memory=user_memory)
    
    # The summary string is already a JSON, so we can save it directly.
    # No need to call separate keyword extraction.
    
    # For embedding, we should use the original content for richness,
    # but the summary can be a good, dense alternative if content is too large.
    # Let's stick with content for now.
    embedding = generate_embedding(content)

    # Attempt to parse the JSON to extract keywords for the database
    try:
        summary_data = json.loads(summary_json_str)
        # Use "suggested_keywords" from the JSON, fall back to an empty list
        keywords = summary_data.get("suggested_keywords", []) 
    except (json.JSONDecodeError, TypeError):
        summary_data = {}
        keywords = []

    content_dict = {
        'url': url,
        'type': file_type,
        'timestamp': timestamp,
        'content': content,
        'summary_json': summary_json_str, # Store the raw JSON summary
        'keywords': keywords,
        'embeddings': embedding,
    }
    
    # Save the processed data to a file
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content_dict, file, indent=4, ensure_ascii=False)

    # Special handling for arxiv PDFs
    if file_type == 'arxiv':
        pdf_file_name = file_path.replace('.json', '.pdf')
        download_arxiv_pdf(url, os.path.dirname(pdf_file_name))
    
    # Special handling for direct PDF downloads
    elif file_type == 'pdf':
        pdf_file_name = file_path.replace('.json', '.pdf')
        download_pdf(url, os.path.dirname(pdf_file_name))
    
    # Append to the legacy index CSV
    with open('saved_text/index.csv', 'a') as index_file:
        index_file.write(f'{file_type},{timestamp},{file_path}\n')
        
    # Return the JSON string and the extracted keywords
    return summary_json_str, keywords

