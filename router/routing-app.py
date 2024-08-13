import streamlit as st
import json
import boto3
from botocore.client import Config
from semantic_router import Route
import os
from semantic_router.encoders import CohereEncoder
from semantic_router import RouteLayer

# Setting page title and header
st.set_page_config(page_title="Aruba Chatbot", page_icon=":robot_face:")
st.title("Aruba Chatbot")

st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)

knowledgeBaseId = '4V4UV8DXOX'
model_id ='anthropic.claude-3-haiku-20240307-v1:0'
os.environ["COHERE_API_KEY"] = "RdXsDWxhX7C8sk5gFkeNYvPbdEtZKIlD81C1NtKt"

bedrock_config = Config(connect_timeout=120, 
                        read_timeout=120, 
                        retries={'max_attempts': 0}
                       )
bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client("bedrock-agent-runtime", config=bedrock_config)

### Set up router
sql_query_assistant = Route(
    name="sql_query_assistant",
    utterances=[
        "Get a list of customers, Employees or albums",
        "What are the albums and tracks that falls under a particular genre"
        ],
    )
architecture_assistant = Route(
        name="architecture_assistant",
        utterances=[
            "What are the 5 pillars of well architected framework",
            "what are the best practices",
            "How to configure AWS service",
            "Tell me about the security pillar",
        ],
    )
routes = [architecture_assistant, sql_query_assistant]

encoder = CohereEncoder()
rl = RouteLayer(encoder=encoder, routes=routes)

### llm router
router_prompt = '''You are a expert in identifying intent from the user question.  
You will read the text provided carefully and determine the intent of the user.  You will then classify the intent in to one of 2 categories - sql_query_assistant or  architecture_assistant.  
If user request is for providing sql query or reading from a table then categorize it as sql_query_assistant.  If user request is for providing guidance, best practices, architecture questions classify them  as architecture_assistant
Respond with just the classification type.  Do NOT add any preamble.'''

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()
    
schema = read_file('chinook.sql')
sql_system_prompt =f'''Transform the following natural language requests into valid SQL queries. Do not add any preamble in your response.  
Assume a database with the following tables and columns exists:
{schema}
'''

def call_llmrouter(prompt, user_query):
    final_prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}: {user_query}"
                    }
                ]
            }
        ]
    }

    final_prompt = json.dumps(final_prompt)
    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=final_prompt,
    )
    response_body = json.loads(response.get('body').read())
    return response_body['content'][0]['text']

def parse_stream(stream):
    for event in stream:
        chunk = event.get('chunk')
        if chunk:
            message = json.loads(chunk.get("bytes").decode())
            if message['type'] == "content_block_delta":
                yield message['delta']['text'] or ""
            elif message['type'] == "message_stop":
                return "\n"
            
def generate_response(prompt, context, system_prompt = ''):
    final_prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}: {context}"
                    }
                ]
            }
        ]
    }
    final_prompt = json.dumps(final_prompt)
    streaming_response = bedrock_client.invoke_model_with_response_stream(
        modelId=model_id,
        body=final_prompt,
    )
    
    stream = streaming_response.get("body")
    st.write_stream(parse_stream(stream))
    st.write_stream(stream)
            
def architecture_assistant(prompt):
    relevant_documents = bedrock_agent_client.retrieve(
    retrievalQuery= {
        'text': prompt
    },
    knowledgeBaseId=knowledgeBaseId,
    retrievalConfiguration= {
        'vectorSearchConfiguration': {
            'numberOfResults': 3 # will fetch top 3 documents which matches closely with the query.
        }
    }
    )

    context = ''
    for doc in relevant_documents['retrievalResults']:
        context += doc['content']['text']
    
    generate_response(prompt, context)

def sql_query_assistant(prompt):
    context= ''
    generate_response(prompt, context, sql_system_prompt)
    
router_type = st.selectbox("Router Type", ["Semantic router", "LLM router"])  
prompt_input = st.text_area("Prompt", key="prompt_data", placeholder= "Enter your Prompt...")
btn_action = st.button("Query")

if btn_action:
    
    if router_type == "Semantic router":
        router = rl(prompt_input).name
    elif router_type == "LLM router":
        router = call_llmrouter(router_prompt, prompt_input)
        
    st.write("I am a " + router)
    
    if router == "architecture_assistant":
        architecture_assistant(prompt_input)
    elif router == "sql_query_assistant":
        sql_query_assistant(prompt_input)