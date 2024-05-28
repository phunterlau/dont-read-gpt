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
def gen_gpt_chat_completion(system_prompt, user_prompt, temp=0.0, engine="gpt-4o", max_tokens=1024,
                            top_p=1, frequency_penalty=0, presence_penalty=0,):
    
    response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role":"system", "content":system_prompt},
                            {"role":"user", "content":user_prompt}],
                    temperature=1,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0)
    return response

def generate_summary(text_snippet, summary_type='general'):

    max_input_words = 100000
    max_input_words_chinese = 50000
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
    #arxiv_paper_prompt = f'You are a scientific researcher. Please provide a concise summary of the following ArXiv paper\'s title and abstract, limit 100 words, addressing the following aspects if available:\n1. Main problem or research question\n2. Key methodology or approach\n3. Main results or findings\n4. Comparison to previous work or state of the art\n5. Potential applications or implications\n6. Limitations or future work'
    #github_repo_prompt = f'You are a scientific researcher. Please provide a concise summary of the following GitHub repository README.md, limit 100 words, addressing the following aspects if available:\n1. Purpose of the project\n2. Key features and benefits\n3. Technology stack or programming languages used\n4. Dependencies or prerequisites\n5. Installation, setup, and usage instructions\n6. Maintenance and main contributors\n7. Known limitations or issues\n8. Project license and usage restrictions\n9. Contribution guidelines\n10. Additional documentation or resources'
    #youtube_prompt = f'You are a scientific researcher. Expert in technical and research content analysis: Summarize the video transcript (150 words max). Cover if available: 1. Main topic. 2. Key concepts/technologies. 3. Primary arguments/points. 4. Significant findings/conclusions. 5. Methodologies/approaches. 6. Examples/case studies. 7. Relation to current trends/knowledge. 8. Counterpoints/alternatives. 9. Future implications/applications. 10. Key quotes/statements. 11. Limitations/weaknesses. 12. Additional resources. 13. Key takeaways.'
    arxiv_paper_prompt = (
    'You are a scientific researcher. Please provide a concise summary of the following ArXiv paper\'s title and abstract, limit 100 words. Include only the aspects that are available:\n'
    '1. Main problem or research question.\n'
    '2. Key methodology or approach.\n'
    '3. Main results or findings.\n'
    '4. Comparison to previous work or state of the art.\n'
    '5. Potential applications or implications.\n'
    '6. Limitations or future work.\n'
    'Note: Exclude any aspects that are not explicitly mentioned in the title or abstract.'
    )
    github_repo_prompt = (
    'You are a scientific researcher. Please provide a concise summary of the following GitHub repository README.md, limit 100 words. Include only the aspects that are available:\n'
    '1. Purpose of the project.\n'
    '2. Key features and benefits.\n'
    '3. Technology stack or programming languages used.\n'
    '4. Dependencies or prerequisites.\n'
    '5. Installation, setup, and usage instructions.\n'
    '6. Maintenance and main contributors.\n'
    '7. Known limitations or issues.\n'
    '8. Project license and usage restrictions.\n'
    '9. Contribution guidelines.\n'
    '10. Additional documentation or resources.\n'
    'Note: Omit any aspects not mentioned in the README.md.'
    )
    youtube_prompt = (
    'You are a scientific researcher and expert in technical and research content analysis. Summarize the video transcript within 150 words. Include only the aspects that are available:\n'
    '1. Main topic.\n'
    '2. Key concepts/technologies.\n'
    '3. Primary arguments/points.\n'
    '4. Significant findings/conclusions.\n'
    '5. Methodologies/approaches.\n'
    '6. Examples/case studies.\n'
    '7. Relation to current trends/knowledge.\n'
    '8. Counterpoints/alternatives.\n'
    '9. Future implications/applications.\n'
    '10. Key quotes/statements.\n'
    '11. Limitations/weaknesses.\n'
    '12. Additional resources.\n'
    '13. Key takeaways.\n'
    'Note: Do not include any aspects that are not covered in the video transcript.'
    )   
    huggingface_model_prompt = (
    'You are an AI expert. Please provide a concise summary of the Hugging Face model page, limit 100 words. Include only the aspects that are available on the page:\n'
    '1. Model Overview: A brief description and primary function of the model.\n'
    '2. Architecture: Type of neural network used.\n'
    '3. Training Data: Key datasets and preprocessing details, if mentioned.\n'
    '4. Performance: Important metrics and benchmark results, if provided.\n'
    '5. Use Cases: Typical applications and examples of implementation, if listed.\n'
    '6. Fine-tuning: Information on adaptability for specific tasks, if available.\n'
    '7. Limitations and Biases: Any known constraints and ethical considerations, if discussed.\n'
    '8. Accessibility: License information and model availability, if specified.\n'
    'Note: Exclude any aspects that are not explicitly mentioned on the model page.'
    )
    ipython_notebook_prompt = (
    'You are a data scientist. Please provide a concise summary of the following IPython notebook, limit 100 words. Include only the aspects that are available:\n'
    '1. Main objectives or goals of the notebook.\n'
    '2. Key data analysis or computational concepts demonstrated.\n'
    '3. Significant findings or results derived from the notebook.\n'
    '4. Code and methodologies used and their significance.\n'
    '5. Any visualizations or graphical representations and their insights.\n'
    '6. Conclusions or potential applications of the notebook\'s content.\n'
    '7. Limitations or areas for further exploration, if mentioned.\n'
    'Note: Focus only on the aspects explicitly included in the notebook.'
    )

    #general_prompt = f'You are a scientific researcher. Please provide a concise concise summary of the following text, limit 100 words, addressing the following aspects if available:\n1. Main topic or subject\n2. Core arguments or points\n3. Significant findings, results, or insights\n4. Comparisons or contrasts with other ideas or studies\n5. Implications or potential applications'
    general_prompt = (
    'You are a scientific researcher. Please provide a concise summary of the following text, limited to 100 words. Include only the aspects that are available:\n'
    '1. Main topic or subject.\n'
    '2. Core arguments or points.\n'
    '3. Significant findings, results, or insights.\n'
    '4. Comparisons or contrasts with other ideas or studies.\n'
    '5. Implications or potential applications.\n'
    'Note: Focus only on the aspects explicitly mentioned in the text.'
    )
    prompts = {
        'arxiv': arxiv_paper_prompt,
        'github': github_repo_prompt,
        'youtube': youtube_prompt,
        'huggingface': huggingface_model_prompt,
        'ipython': ipython_notebook_prompt,
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
    try:
        response = gen_gpt_chat_completion(system_prompt, user_prompt, max_tokens=max_output_tokens)

        #summary = response.choices[0].text.strip()
        summary = response.choices[-1].message.content.strip()
        return summary
    except openai.BadRequestError as e:
        # Check if the error is due to exceeding maximum context length
        if "maximum context length" in str(e):
            error_message = "The input is too long. Please reduce the length and try again."
        else:
            error_message = "An error occurred: " + str(e)
        return error_message

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
    try:
        response = gen_gpt_chat_completion(system_prompt, user_prompt, max_tokens=256)

        #keywords = response.choices[0].text.strip().split(', ')
        keywords = response.choices[-1].message.content.strip().split(', ')
        return keywords
    except openai.BadRequestError as e:
        # Check if the error is due to exceeding maximum context length
        if "maximum context length" in str(e):
            error_message = "The input is too long. Please reduce the length and try again."
        else:
            error_message = "An error occurred: " + str(e)
        return error_message

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