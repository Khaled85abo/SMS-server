from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, AIMessage

gpt4_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# chain_gpt_35 = ChatOpenAI(model="gpt-3.5-turbo", max_tokens=1024)
chain_gpt_4_vision = ChatOpenAI(model="gpt-4-vision-preview", max_tokens=1024)

async def generate_response(prompt):
    response = await llm.invoke(prompt)
    return response.content


# Function for text summaries
def summarize_text(text_element):
    prompt = f"Summarize the following text:\n\n{text_element}\n\nSummary:"
    response = gpt4_mini.invoke([HumanMessage(content=prompt)])
    return response.content

# Function for table summaries
def summarize_table(table_element):
    prompt = f"Summarize the following table:\n\n{table_element}\n\nSummary:"
    response = gpt4_mini.invoke([HumanMessage(content=prompt)])
    return response.content

