from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from groq import Groq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import dotenv_values

#Load API key securely from .env file
env_values = dotenv_values(".env")
GroqAPIKey = env_values.get("GroqAPIKey")

#Initialize Groq client
client = Groq(api_key=GroqAPIKey)

#Prompt Template
template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully: \n\n"
    "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
    "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
    "3. **Empty Response:** If no information matches the description, return an empty string ('')."
    "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
    "5. **No Extra Data:** If you see any data is repeating and not relevant to question remove it."
)

template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully: \n\n"
    "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
    "2. **Be Specific:** If the description asks for a publication date, return the 'Published online' date if available. "
    "3. **No Extra Content:** Do not include comments or explanations in your response. "
    "4. **Empty Response:** If no information matches the description, return an empty string ('')."
    "5. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
    "6. **No Repetition:** Do not repeat unrelated content."
)


prompt = ChatPromptTemplate.from_template(template)

def parse_with_groq(dom_chunks, parse_description):
    parsed_results = []

    for i, chunk in enumerate(dom_chunks, start=1):
        rendered_prompt = template.format(dom_content=chunk, parse_description=parse_description)
        #rendered_prompt = prompt.format(dom_content=chunk, parse_description=parse_description).to_string()

        try:
            response = client.chat.completions.create(
                model= 'llama3-8b-8192', #"mixtral-8x7b-32768",  # or "llama3-8b-8192"
                messages=[
                    {"role": "user", "content": rendered_prompt}
                ],
                temperature=0.5
            )
            output = response.choices[0].message.content.strip()
            print(f"Parsed batch {i} of {len(dom_chunks)}")
            parsed_results.append(output)
        except Exception as e:
            print(f"Error parsing batch {i}: {e}")
            parsed_results.append("")

    return "\n".join(parsed_results)

'''
template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully: \n\n"
    "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
    "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
    "3. **Empty Response:** If no information matches the description, return an empty string ('')."
    "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
)

model = OllamaLLM(model='llama3')
'''
'''
def parse_with_ollama(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model 

    parsed_results = []

    for i, chunk in enumerate(dom_chunks, start=1):
        respone = chain.invoke({"dom_content": chunk, "parse_description": parse_description})

        print(f"Parsed batch {i} of {len(dom_chunks)}")
        parsed_results.append(response)

    return "\n".join(parsed_results)
'''

