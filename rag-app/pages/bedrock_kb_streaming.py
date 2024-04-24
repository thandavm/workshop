import streamlit as st
import json
import boto3

knowledgeBaseId = '4V4UV8DXOX'
model_id ='anthropic.claude-3-haiku-20240307-v1:0'

bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client("bedrock-agent-runtime")

def parse_stream(stream):
    for event in stream:
        chunk = event.get('chunk')
        if chunk:
            message = json.loads(chunk.get("bytes").decode())
            if message['type'] == "content_block_delta":
                yield message['delta']['text'] or ""
            elif message['type'] == "message_stop":
                return "\n"

def generate_response(prompt, context):
    final_prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
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

def generate_response_from_oss(prompt):
    ## retrieve top 3 documents
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
    
    ## concatenate the results
    context = ''
    for doc in relevant_documents['retrievalResults']:
        context += doc['content']['text']
    
    ## generate response
    generate_response(prompt, context)

prompt_input = st.text_area("Prompt", key="prompt_data", placeholder= "Enter your Prompt...")
btn_action = st.button("Query")

if btn_action:
    generate_response_from_oss(prompt_input)

