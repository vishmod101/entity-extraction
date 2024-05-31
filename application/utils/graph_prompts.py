import os
from openai import AzureOpenAI
import dotenv
import streamlit as st
import yaml
from yaml.loader import SafeLoader
from utils.auth_utils import(
    hash_plaintext_passwords,
    save_config
)

dotenv.load_dotenv()

# client = AzureOpenAI(
#     azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
#     api_key = os.getenv("OPENAI_KEY"),   
#     api_version = os.getenv("OPENAI_API_VERSION"), 
# )

#Initialise the session 
def initialize_session_state():
    if "config" not in st.session_state:
        with open('auth.yaml') as file:
            st.session_state.config = yaml.load(file, Loader=SafeLoader)
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = ""
    # if 'hashed_done' not in st.session_state:
    #     config = hash_plaintext_passwords(st.session_state.config)
    #     save_config(config)
    #     st.session_state.config = config
    #     st.session_state.hashed_done = True

initialize_session_state()

client = AzureOpenAI(
    azure_endpoint = st.session_state.config['azure_openai']['endpoint'], 
    api_key = st.session_state.config['azure_openai']['api_key'],   
    api_version = st.session_state.config['azure_openai']['api_version']
)


def knowledge_graph_v1(ent_list: list, input: str):

    SYS_PROMPT = ("You are a network graph maker who extracts terms and their relations from a given context. "
        "You are provided with a list of entities and some text."
        "Your task is to extract the ontology of terms mentioned in the given context relating to the entities in the list."
        "Thought 1: While traversing through each sentence, Think about the key terms mentioned in it.\n"
            "\tTerms may include person (agent), location, organization, date, duration, \n"
            "\tcondition, concept, object, entity  etc.\n"
            "\tTerms should be as atomistic as possible\n"
        "Thought 2: Think about how these terms can have one on one relation with other terms.\n"
            "\tTerms that are mentioned in the same sentence or the same paragraph are typically related to each other.\n"
            "\tTerms can be related to many other terms\n"
        "Thought 3: Find out the relation between each such related pair of terms. \n"
        "Return this list as valid JSON like the following: \n"
        "{ \n"
        "  graph:[ \n"
        "   {\n"
        '       "node_1": "A concept from extracted ontology",\n'
        '       "node_2": "A related concept from extracted ontology",\n'
        '       "edge": "relationship between the two concepts, node_1 and node_2 in one or two sentences"\n' 
        "   }, {...}\n"
        " ] \n"
        "}"
    )

    USER_PROMPT = f"entity_list: ```{ent_list}```, context: ```{input}``` \n\n output: "

    messages=[
      {"role": "system", "content": f"{SYS_PROMPT}"},
      {"role": "user", "content": f"{USER_PROMPT}"}
    ]

    response = client.chat.completions.create(model="gpt-35-turbo", messages=messages)
                                            #   response_format={ "type": "json_object" },
                                            #   messages=messages)

    return response.choices[0].message.content