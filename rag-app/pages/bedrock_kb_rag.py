import streamlit as st
import json
import boto3

knowledgeBaseId = '4V4UV8DXOX'
model_id = 'anthropic.claude-v2'

bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client("bedrock-agent-runtime")

def generate_response(prompt):
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
    final_prompt = f"""Human: You are a helpful, polite, fact-based agent.
    If you don't know the answer, just say that you don't know.
    Please answer the following question using the context provided. 

    CONTEXT: 
    {context}
    =========
    QUESTION: {prompt} 
    
    
    Assistant:
    """
    
    body = json.dumps({"prompt": final_prompt, 
                    "max_tokens_to_sample": 250})

    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock_client.invoke_model(body=body, 
                                            modelId=model_id, 
                                            accept=accept, 
                                            contentType=contentType)
    
    response_body = json.loads(response.get('body').read())
    print(response_body)
    return response_body['completion']


model_type = st.selectbox("Model:", ["Claude 2", "Claude 3"])
prompt_input = st.text_area("Prompt", key="prompt_data", placeholder= "Enter your Prompt...")
btn_action = st.button("Query")

if btn_action:
    result = generate_response(prompt_input)
    st.write(result)


#### sample questions
### What are the 5 pillars of well architected framework
