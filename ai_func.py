import os
import openai
import re

openai.api_key = os.environ['OPENAI_KEY']

def is_chinese(text):
    if any(u'\u4e00' <= c <= u'\u9fff' for c in text):
        return True
    return False

def generate_summary(text_snippet, summary_type='general'):

    max_input_words = 1500
    max_input_words_chinese = 1000
    max_output_tokens = 1000
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

    arxiv_paper_prompt = f'Please provide a summary of the following ArXiv paper\'s title and abstract, addressing the following aspects:\n1. Main problem or research question\n2. Key methodology or approach\n3. Main results or findings\n4. Comparison to previous work or state of the art\n5. Potential applications or implications\n6. Limitations or future work\n\n{text_snippet}\n\nSummary:'
    github_repo_prompt = f'Please provide a summary of the following GitHub repository README.md, addressing the following aspects:\n1. Purpose of the project\n2. Key features and benefits\n3. Technology stack or programming languages used\n4. Dependencies or prerequisites\n5. Installation, setup, and usage instructions\n6. Maintenance and main contributors\n7. Known limitations or issues\n8. Project license and usage restrictions\n9. Contribution guidelines\n10. Additional documentation or resources\n\n{text_snippet}\n\nSummary:'
    general_prompt = f'Please provide a concise summary of the following text, addressing the following aspects:\n1. Main topic or subject\n2. Core arguments or points\n3. Significant findings, results, or insights\n4. Comparisons or contrasts with other ideas or studies\n5. Implications or potential applications\n\n{text_snippet}\n\nSummary:'
    prompts = {
        'arxiv': arxiv_paper_prompt,
        'github': github_repo_prompt,
        'general': general_prompt,

    }

    prompt = prompts.get(summary_type, prompts['general'])

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=max_output_tokens,
        n=1,
        stop=None,
        temperature=0.5,
    )

    summary = response.choices[0].text.strip()

    return summary

def generate_embedding(text_snippet):
    embedding = openai.Embedding.create(
        input=text_snippet, model="text-embedding-ada-002"
    )["data"][0]["embedding"]
    return embedding

def extract_keywords_from_summary(summary):
    prompt = (
        f"Given the following summary, identify important keywords or phrases that would be suitable for creating internal links in Obsidian. These keywords should represent the main concepts, topics, or entities in the summary:\n\n{summary}\n\n"
        f"Obsidian Keywords:"
    )
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )

    keywords = response.choices[0].text.strip().split(', ')
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