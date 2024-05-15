import streamlit as st
import boto3
import uuid

## TODO
agent_alias_id = 'A7UMT32VN4'
agent_id = '0MESIB6SRG'

bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client("bedrock-agent-runtime")

def header():
    """
    App Header setting
    """
    # --- Set up the page ---
    st.set_page_config(
        page_title="Amazon Bedrock Chatbot",
        page_icon=":computer:",
        layout="centered",
    )

    st.markdown("# Chatbot - Agent")
    
def show_footer() -> None:
    st.markdown(
        "<div style='text-align: right'> © 2023 Amazon Web Services </div>",
        unsafe_allow_html=True,
    )

def initialization():
    # --- Initialize session_state ---
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid1())
        st.session_state.questions = []
        st.session_state.answers = []

    if "temp" not in st.session_state:
        st.session_state.temp = ""

    # Initialize cache in session state
    if "cache" not in st.session_state:
        st.session_state.cache = {}

def clear_input():
    st.session_state.session_id = str(uuid.uuid1())
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state["temp"] = st.session_state["input"]
    st.session_state["input"] = ""
    
def show_empty_container(height: int = 100) -> st.container:
    empty_placeholder = st.empty()
    with empty_placeholder.container():
        st.markdown("<br>" * height, unsafe_allow_html=True)
    return empty_placeholder

def get_response(prompt, session_id):

    agentResponse = bedrock_agent_client.invoke_agent(
        inputText=prompt,
        agentId=agent_id,
        agentAliasId=agent_alias_id, 
        sessionId=session_id,
    )

    event_stream = agentResponse['completion']
    for event in event_stream:        
        if 'chunk' in event:
            data = event['chunk']['bytes']
            agent_answer = data.decode('utf8')
            end_event_received = True

    return agent_answer, session_id

    
def show_message():
    # --- Start the session when there is user input ---
    # Start a new conversation

    new_conversation = st.button("New Conversation", key="clear", on_click=clear_input)

    user_input = st.text_input("# **Question:** 👇", "", key="input")
    print(f"user_input: {user_input}")
    
    if new_conversation:
        st.session_state.session_id = str(uuid.uuid1())
        st.session_state.user_input = ""

    if user_input:
        session_id = st.session_state.session_id
                        
        with st.spinner("Gathering info ..."):
            vertical_space = show_empty_container()
            vertical_space.empty()
            response_output, current_session = get_response(user_input, session_id)

            st.write("-------")

            answer = "**Answer**: \n\n" + response_output
            st.session_state.session_id = current_session
            st.session_state.questions.append(user_input)
            st.session_state.answers.append(answer)

    if st.session_state["answers"]:
        for i in range(len(st.session_state["answers"]) - 1, -1, -1):
            with st.chat_message(
                name="human",
                avatar="https://api.dicebear.com/7.x/notionists-neutral/svg?seed=Felix",
            ):
                st.markdown(st.session_state["questions"][i])

            with st.chat_message(
                name="ai",
                avatar="https://assets-global.website-files.com/62b1b25a5edaf66f5056b068/62d1345ba688202d5bfa6776_aws-sagemaker-eyecatch-e1614129391121.png",
            ):
                st.markdown(st.session_state["answers"][i])

def main():
    """
    Streamlit APP
    """
    # --- Section 1 ---
    header()
    # --- Section 2 ---
    initialization()
    # --- Section 3 ---
    show_message()
    # --- Foot Section ---
    show_footer()

if __name__ == "__main__":
    main()