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

# Use gpt-3.5-turbo-16k-0613 for longer text and chat completion
@backoff.on_exception(
    partial(backoff.expo, max_value=50),
    (openai.RateLimitError, openai.APIError, openai.APIConnectionError),
)
def gen_gpt_chat_completion(system_prompt, user_prompt, temp=0.0, engine="gpt-3.5-turbo-16k-0613", max_tokens=1024,
                            top_p=1, frequency_penalty=0, presence_penalty=0,):
    
    response = client.chat.completions.create(
                    model="gpt-3.5-turbo-16k-0613",
                    messages=[{"role":"system", "content":system_prompt},
                            {"role":"user", "content":user_prompt}],
                    temperature=1,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0)
    return response

def generate_summary(text_snippet, summary_type='general'):

    max_input_words = 10000
    max_input_words_chinese = 5000
    max_output_tokens = 1024
    total_tokens = 4097  # Assuming an average of 2 tokens per word

    if total_tokens > 4097:
        raise ValueError("The total number of tokens (input + output) must not exceed 4097.")

    # Truncate the text snippet if it's too long
    words = text_snippet.split()
    # for non-English text, we need to use a different method to split the text into words and fit the token size
    if is_chinese(text_snippet):
        text_snippet = text_snippet[:max_input_words_chinese]
    elif len(words) > max_input_words:
        words = words[:max_input_words]
        text_snippet = " ".join(words)

    #arxiv_paper_prompt = f'Please provide a summary of the following ArXiv paper\'s title and abstract within 450 chars, addressing the following aspects:\n1. Main problem or research question\n2. Key methodology or approach\n3. Main results or findings\n4. Comparison to previous work or state of the art\n5. Potential applications or implications\n6. Limitations or future work\n\n{text_snippet}\n\nSummary:'
    #github_repo_prompt = f'Please provide a summary of the following GitHub repository README.md· within 450 chars, addressing the following aspects:\n1. Purpose of the project\n2. Key features and benefits\n3. Technology stack or programming languages used\n4. Dependencies or prerequisites\n5. Installation, setup, and usage instructions\n6. Maintenance and main contributors\n7. Known limitations or issues\n8. Project license and usage restrictions\n9. Contribution guidelines\n10. Additional documentation or resources\n\n{text_snippet}\n\nSummary:'
    #general_prompt = f'Please provide a concise summary of the following text within 380 chars, addressing the following aspects:\n1. Main topic or subject\n2. Core arguments or points\n3. Significant findings, results, or insights\n4. Comparisons or contrasts with other ideas or studies\n5. Implications or potential applications\n\n{text_snippet}\n\nSummary:'
    arxiv_paper_prompt = f'You are a scientific researcher. Please provide a concise summary of the following ArXiv paper\'s title and abstract, limit 100 words, addressing the following aspects if availble:\n1. Main problem or research question\n2. Key methodology or approach\n3. Main results or findings\n4. Comparison to previous work or state of the art\n5. Potential applications or implications\n6. Limitations or future work'
    github_repo_prompt = f'You are a scientific researcher. Please provide a concise summary of the following GitHub repository README.md, limit 100 words, addressing the following aspects if availble:\n1. Purpose of the project\n2. Key features and benefits\n3. Technology stack or programming languages used\n4. Dependencies or prerequisites\n5. Installation, setup, and usage instructions\n6. Maintenance and main contributors\n7. Known limitations or issues\n8. Project license and usage restrictions\n9. Contribution guidelines\n10. Additional documentation or resources'
    youtube_prompt = f'You are a scientific researcher. Expert in technical and research content analysis: Summarize the video transcript (150 words max). Cover if availble: 1. Main topic. 2. Key concepts/technologies. 3. Primary arguments/points. 4. Significant findings/conclusions. 5. Methodologies/approaches. 6. Examples/case studies. 7. Relation to current trends/knowledge. 8. Counterpoints/alternatives. 9. Future implications/applications. 10. Key quotes/statements. 11. Limitations/weaknesses. 12. Additional resources. 13. Key takeaways.'
    general_prompt = f'You are a scientific researcher. Please provide a concise concise summary of the following text, limit 100 words, addressing the following aspects if availble:\n1. Main topic or subject\n2. Core arguments or points\n3. Significant findings, results, or insights\n4. Comparisons or contrasts with other ideas or studies\n5. Implications or potential applications'
    prompts = {
        'arxiv': arxiv_paper_prompt,
        'github': github_repo_prompt,
        'youtube': youtube_prompt,
        'general': general_prompt,

    }

    system_prompt = prompts.get(summary_type, prompts['general'])
    user_prompt = text_snippet

    #response = openai.Completion.create(
    #    engine='text-davinci-003',
    #    prompt=prompt,
    #    max_tokens=max_output_tokens,
    #    n=1,
    #    stop=None,
    #    temperature=0.5,
    #)
    #response = gen_gpt_completion(prompt, max_tokens=max_output_tokens)
    response = gen_gpt_chat_completion(system_prompt, user_prompt, max_tokens=max_output_tokens)

    #summary = response.choices[0].text.strip()
    summary = response.choices[-1].message.content.strip()

    return summary

def generate_embedding(text_snippet):
    #embedding = openai.Embedding.create(
    #    input=text_snippet, model="text-embedding-ada-002"
    #)["data"][0]["embedding"]
    embedding = client.embeddings.create(
        input=text_snippet, model="text-embedding-ada-002"
    ).data[0].embedding
    return embedding

def extract_keywords_from_summary(summary):
    prompt = (
        f"Given the following summary, identify important keywords or phrases that would be suitable for creating internal links in Obsidian. These keywords should represent the main concepts, topics, or entities in the summary.\n\n"
        f"Please provide a list of Obsidian Keywords, separated by commas:"
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
    response = gen_gpt_chat_completion(system_prompt, user_prompt, max_tokens=256)

    #keywords = response.choices[0].text.strip().split(', ')
    keywords = response.choices[-1].message.content.strip().split(', ')
    return keywords

def summary_to_obsidian_markdown(summary, keywords):
    not_found_keywords = []

    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        matches = pattern.findall(summary)
        if matches:
            summary = pattern.sub(f"[[{keyword}]]", summary)
        else:
            not_found_keywords.append(keyword)
    
    if not_found_keywords:
        additional_keywords = ", ".join(f"[[{keyword}]]" for keyword in not_found_keywords)
        summary += f"\n\nAdditional Keywords: {additional_keywords}"
    
    return summary

def test_obsidian_markdown():
    summary = "This is a summary of a paper about the use of AI in the field of medicine. The paper discusses the use of AI to diagnose diseases and predict the effectiveness of treatments. The paper also discusses the use of AI to predict the effectiveness of treatments for diseases such as cancer and diabetes. The paper also discusses the use of AI to predict the effectiveness of treatments for diseases such as cancer and diabetes. The paper also discusses the use of AI to predict the effectiveness of treatments for diseases such as cancer and diabetes. The paper also discusses the use of AI to predict the effectiveness of treatments for diseases such as cancer and diabetes. The paper also discusses the use of AI to predict the effectiveness of treatments for diseases such as cancer and diabetes. The paper also discusses the use of AI to predict the effectiveness of treatments for diseases such as cancer and diabetes."
    keywords = extract_keywords_from_summary(summary)
    result = summary_to_obsidian_markdown(summary, keywords)
    print(keywords, result)

if __name__ == '__main__':
    test_obsidian_markdown()