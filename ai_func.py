import os
import openai
import re
import backoff
from functools import partial

openai.api_key = os.environ['OPENAI_KEY']
client = openai.OpenAI(api_key=os.environ['OPENAI_KEY'])

def is_chinese(text):
    if any(u'\u4e00' <= c <= u'\u9fff' for c in text):
        return True
    return False

# Retry with exponential backoff just in case OpenAI API is temporarily unavailable
@backoff.on_exception(
    partial(backoff.expo, max_value=50),
    (openai.RateLimitError, openai.APIError, openai.APIConnectionError),
)
def gen_gpt_completion(prompt, temp=0.0, engine="text-davinci-003", max_tokens=100, 
                       top_p=1, frequency_penalty=0, presence_penalty=0,):
    response = client.completions.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.5,
        top_p=1,
        stop = None,
        #frequency_penalty=0.5,
        #presence_penalty=0.5,
    )
    return response

# Use gpt-40o for longer text and chat completion
#@backoff.on_exception(
#    partial(backoff.expo, max_value=2),
#    (openai.RateLimitError, openai.APIError, openai.APIConnectionError),
#)
def gen_gpt_chat_completion(system_prompt, user_prompt, temp=0.0, engine="gpt-4o", max_tokens=2048,
                            top_p=1, frequency_penalty=0, presence_penalty=0, use_json_mode=False):
    
    model_to_use = "gpt-4o-mini" if "gpt-4o-mini" in engine else "gpt-4o"
    
    request_params = {
        "model": model_to_use,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty
    }
    
    if use_json_mode:
        request_params["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**request_params)
    return response

def generate_summary(text_snippet, summary_type='general', focus=None, use_arxiv_prompt=False, user_memory=None):

    max_input_words = 150000  # Increased limit for more powerful models
    max_input_words_chinese = 75000
    max_output_tokens = 2048

    # ... (rest of the function remains the same until prompts) ...

    # Truncate the text snippet if it's too long
    words = text_snippet.split()
    if is_chinese(text_snippet):
        text_snippet = text_snippet[:max_input_words_chinese]
    elif len(words) > max_input_words:
        words = words[:max_input_words]
        text_snippet = " ".join(words)

    # Choose prompt based on whether this is an arXiv paper
    if use_arxiv_prompt:
        # Specialized arXiv academic paper analysis prompt
        json_prompt_structure = """
        You are an academic research analyst AI specializing in arXiv papers. Your task is to provide a comprehensive analysis of the provided academic paper in English.

        JSON Schema:
        {
          "title": "The main title of the paper.",
          "one_sentence_summary": "A single, concise sentence that captures the core essence of the paper in English.",
          "suggested_keywords": ["A list of 5-7 relevant academic keywords or key phrases."],
          "main_point": "The central thesis or main argument of the paper (max 80 words).",
          "innovation": "What novel contributions or innovations this paper presents (max 80 words).",
          "contribution": "The specific contributions to the field or state of knowledge (max 80 words).",
          "improvement": "How this work improves upon existing methods or understanding (max 60 words).",
          "limitations": "Limitations, weaknesses, or areas for improvement identified (max 60 words).",
          "insights": "Key insights, implications, or takeaways from this work (max 60 words).",
          "one_line_summary": "A single impactful sentence that summarizes the entire paper (max 40 words)."
        }

        Instructions:
        - Analyze the paper comprehensively but concisely
        - All responses must be in English
        - Stay within the specified word limits for each section (max 400 words total)
        - Focus on academic rigor and clarity
        - If a section's content is not clearly present in the text, provide "Not clearly specified" for that field
        - Extract the actual paper title when possible
        - Keywords should be academic and searchable terms
        """
        
        # Add personalization section if user memory is provided
        if user_memory and user_memory.strip():
            json_prompt_structure += f"""
        
        PERSONALIZATION INSTRUCTION:
        Based on the user's research interests provided below, add a section in your JSON output with the key "why_you_should_read". 
        This section should explain why the paper is relevant to the user's specific interests and research focus. 
        If the paper is not clearly relevant to their interests, omit this key entirely.
        Keep this section concise but compelling (max 100 words).
        
        User's Research Interests: {user_memory.strip()}
        """
    else:
        # Regular JSON prompt structure for non-arXiv content
        json_prompt_structure = """
        You are a research analyst AI. Your task is to extract the most critical information from the provided text and structure it as a JSON object.

        JSON Schema:
        {
          "title": "The main title of the document.",
          "one_sentence_summary": "A single, concise sentence that captures the core essence of the document.",
          "suggested_keywords": ["A list of 5-7 relevant keywords or key phrases that categorize the content."],
          "key_takeaways": ["A list of 3-5 bullet points representing the most important insights or findings."],
          "methodology": "A brief description of the methodology, tools, or approach used. Omit if not applicable.",
          "results": "A brief description of the key results or outcomes. Omit if not applicable.",
          "critique_and_limitations": "A brief, constructive critique of the work, mentioning any limitations or potential weaknesses. Omit if not mentioned.",
          "confidence_score": "A float between 0.0 and 1.0 indicating your confidence in the accuracy and completeness of this summary based on the source text."
        }

        Instructions:
        - Adhere strictly to the JSON schema.
        - If a field's content is not present in the text, omit the key from the JSON object.
        - The "title" should be extracted or inferred from the text.
        - The "key_takeaways" should be distinct, impactful points.
        - The "suggested_keywords" should be specific and relevant.
        """

    if focus:
        json_prompt_structure += f"\n- Pay special attention to the following aspect and ensure it is covered in the summary: '{focus}'"

    system_prompt = json_prompt_structure
    user_prompt = f"Here is the text to summarize:\n\n---\n\n{text_snippet}"

    try:
        response = gen_gpt_chat_completion(
            system_prompt, 
            user_prompt, 
            max_tokens=max_output_tokens, 
            use_json_mode=True,
            temp=0.2 # A little creativity for better summaries
        )
        
        summary_json = response.choices[-1].message.content.strip()
        
        # Basic validation if it's a string that looks like JSON
        if summary_json.startswith('{') and summary_json.endswith('}'):
            return summary_json
        else:
            # Fallback to text if JSON parsing fails
            escaped_summary = summary_json.replace('"', "'").replace('\n', ' ')
            return f'{{"title": "Summary", "one_sentence_summary": "{escaped_summary}"}}'

    except openai.BadRequestError as e:
        # ... (error handling remains the same) ...
        if "maximum context length" in str(e):
            error_message = "The input is too long. Please reduce the length and try again."
        else:
            error_message = "An error occurred: " + str(e)
        return '{"error": "' + error_message.replace('"', "'") + '"}'
    except Exception as e:
        error_msg = str(e).replace('"', "'")
        return '{"error": "An unexpected error occurred: ' + error_msg + '"}'

def process_user_memory(existing_profile: str, new_memory_input: str) -> str:
    """
    Process and synthesize user memory using GPT-4o-mini.
    Takes existing profile and new memory input, returns updated profile.
    """
    system_prompt = """You are a research assistant specializing in understanding and synthesizing user research preferences and interests.

Your task is to take a user's existing research profile and a new research interest they've provided, then create a single, coherent, updated profile that captures their comprehensive research interests.

Guidelines:
1. If no existing profile is provided, create a new profile based solely on the new interest
2. If an existing profile exists, intelligently merge the new interest with the existing one
3. Look for overlapping themes, complementary areas, and natural connections
4. Maintain the user's specific terminology and preferences where possible
5. Keep the profile concise but comprehensive (aim for 2-4 sentences, max 200 words)
6. Focus on research areas, methodologies, topics, and academic interests
7. Avoid redundancy - don't repeat the same concepts multiple times
8. Create a narrative flow that shows the breadth and depth of their interests

Output format: Return only the updated research profile text, no additional commentary or formatting."""

    if existing_profile and existing_profile.strip():
        user_prompt = f"""Existing Profile: {existing_profile.strip()}

New Interest: {new_memory_input.strip()}

Please synthesize these into a single, updated research profile."""
    else:
        user_prompt = f"""New Interest: {new_memory_input.strip()}

Please create a research profile based on this interest."""

    try:
        response = gen_gpt_chat_completion(
            system_prompt, 
            user_prompt, 
            max_tokens=300,
            engine="gpt-4o-mini",
            temp=0.3  # Slight creativity for better synthesis
        )
        
        updated_profile = response.choices[-1].message.content.strip()
        return updated_profile
        
    except Exception as e:
        # Fallback: If AI processing fails, combine manually
        if existing_profile and existing_profile.strip():
            return f"{existing_profile.strip()} Additionally interested in: {new_memory_input.strip()}"
        else:
            return new_memory_input.strip()

def generate_personalized_section(document_content: str, user_memory: str) -> str:
    """
    Generate a personalized "Why You Should Read This" section for an existing document.
    This is a lightweight call specifically for cached documents.
    
    Args:
        document_content: The content or summary of the document
        user_memory: The user's research interests profile
    
    Returns:
        Personalized text explaining why the user should read this, or empty string if not relevant
    """
    system_prompt = """You are a research assistant specializing in personalized academic recommendations.

Your task is to analyze a research document and determine if it's relevant to a user's specific research interests. If it is relevant, provide a concise explanation of why they should read it.

Guidelines:
1. Focus on connections between the document's content and the user's interests
2. Be specific about what aspects would be most valuable to the user
3. Keep the response concise but compelling (max 100 words)
4. If the document is not clearly relevant to their interests, return "NOT_RELEVANT"
5. Look for both direct matches and potential interdisciplinary connections
6. Consider methodology, applications, and theoretical contributions that align with their interests

Output format: Return either a personalized recommendation or "NOT_RELEVANT"."""

    user_prompt = f"""Document Content/Summary: {document_content[:2000]}

User's Research Interests: {user_memory}

Please analyze if this document is relevant to the user's interests and provide a personalized recommendation if appropriate."""

    try:
        response = gen_gpt_chat_completion(
            system_prompt, 
            user_prompt, 
            max_tokens=150,
            engine="gpt-4o-mini",
            temp=0.3
        )
        
        result = response.choices[-1].message.content.strip()
        
        # Check if the AI determined the document is not relevant
        if "NOT_RELEVANT" in result.upper():
            return ""
        
        return result
        
    except Exception as e:
        # Fail silently for personalization - don't break the main flow
        return ""

def generate_embedding(text_snippet):
    #embedding = openai.Embedding.create(
    #    input=text_snippet, model="text-embedding-ada-002"
    #)["data"][0]["embedding"]
    embedding = client.embeddings.create(
        input=text_snippet[:8192], model="text-embedding-ada-002"
    ).data[0].embedding
    return embedding

def extract_keywords_from_summary(summary):
    prompt = (
        "You are an expert knowledge management assistant specializing in extracting meaningful keywords for research databases and knowledge graphs.\n\n"
        "From the following summary, identify the most important keywords and phrases that capture:\n"
        "1. Core concepts and technical terms\n"
        "2. Technologies, tools, and methodologies mentioned\n"
        "3. Research areas and academic fields\n"
        "4. Key entities (organizations, people, products, datasets)\n"
        "5. Important processes or approaches\n\n"
        "Guidelines:\n"
        "- Focus on substantive, searchable terms (avoid generic words like 'study', 'research', 'paper')\n"
        "- Include both specific technical terms and broader conceptual keywords\n"
        "- Use the exact terminology from the text when possible\n"
        "- Prefer noun phrases over single words when they represent complete concepts\n"
        "- Limit to 8-12 most relevant keywords\n\n"
        "Format: Return only the keywords separated by commas, no additional text or explanations.\n"
        "Example output: Machine Learning, Natural Language Processing, Transformer Architecture, BERT, Sentiment Analysis"
    )
    #response = openai.Completion.create(
    #    engine="text-davinci-003",
    #    prompt=prompt,
    #    max_tokens=100,
    #    n=1,
    #    stop=None,
    #    temperature=0.5,
    #)
    system_prompt = prompt
    user_prompt = summary
    #response = gen_gpt_completion(prompt, max_tokens=100)
    try:
        response = gen_gpt_chat_completion(system_prompt, user_prompt, max_tokens=256)

        # Extract keywords from response and clean them up
        keywords_text = response.choices[-1].message.content.strip()
        
        # Remove any leading text and get just the keywords
        if ':' in keywords_text:
            keywords_text = keywords_text.split(':', 1)[1].strip()
        
        # Split by commas and clean each keyword
        keywords = [kw.strip().strip('"').strip("'") for kw in keywords_text.split(',')]
        
        # Filter out empty keywords and very short ones
        keywords = [kw for kw in keywords if len(kw.strip()) > 2]
        
        return keywords
    except openai.BadRequestError as e:
        # Check if the error is due to exceeding maximum context length
        if "maximum context length" in str(e):
            error_message = "The input is too long. Please reduce the length and try again."
        else:
            error_message = "An error occurred: " + str(e)
        return error_message

def download_youtube_transcript(video_id):
    """
    Downloads a YouTube video transcript using youtube_transcript_api.
    Returns the transcript text or error message.
    
    Args:
        video_id (str): YouTube video ID (e.g., 'dQw4w9WgXcQ' from youtube.com/watch?v=dQw4w9WgXcQ)
    
    Returns:
        str: Transcript text or error message
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine transcript segments into full text
        transcript_text = ' '.join([item['text'] for item in transcript_list])
        
        return transcript_text
        
    except Exception as e:
        return f"Error downloading transcript: {str(e)}"

def summary_to_obsidian_markdown(summary, keywords):
    """
    Convert a summary to Obsidian markdown format by wrapping keywords in [[]] links.
    Improved to handle better keyword matching and formatting.
    """
    processed_summary = summary
    not_found_keywords = []

    for keyword in keywords:
        # Clean up the keyword (remove extra quotes, whitespace)
        clean_keyword = keyword.strip().strip('"').strip("'")
        if not clean_keyword:
            continue
            
        # Create case-insensitive pattern for exact and partial matching
        # Handle both exact matches and possessive forms
        patterns = [
            re.compile(r'\b' + re.escape(clean_keyword) + r'\b', re.IGNORECASE),
            re.compile(r'\b' + re.escape(clean_keyword) + r's\b', re.IGNORECASE),  # plural
        ]
        
        found_match = False
        for pattern in patterns:
            if pattern.search(processed_summary):
                # Replace only if not already wrapped in [[]]
                def replace_func(match):
                    text = match.group(0)
                    if not (processed_summary[max(0, match.start()-2):match.start()] == '[[' and 
                           processed_summary[match.end():match.end()+2] == ']]'):
                        return f"[[{clean_keyword}]]"
                    return text
                
                processed_summary = pattern.sub(replace_func, processed_summary)
                found_match = True
                break
        
        if not found_match:
            not_found_keywords.append(clean_keyword)
    
    # Add additional keywords section for important terms not found in text
    if not_found_keywords:
        additional_keywords = ", ".join(f"[[{keyword}]]" for keyword in not_found_keywords)
        processed_summary += f"\n\nAdditional Keywords: {additional_keywords}"
    
    return processed_summary

def test_obsidian_markdown():
    """Test the improved Obsidian markdown conversion with better keywords."""
    summary = "This paper introduces MLCopilot, a framework for automating machine learning pipelines using large language models like ChatGPT. The system demonstrates competitive programming capabilities and automates hyperparameter optimization in various AI applications."
    
    print("Testing improved keyword extraction and Obsidian markdown conversion...")
    keywords = extract_keywords_from_summary(summary)
    print(f"Extracted keywords: {keywords}")
    
    result = summary_to_obsidian_markdown(summary, keywords)
    print(f"Obsidian markdown result:\n{result}")

if __name__ == '__main__':
    test_obsidian_markdown()
