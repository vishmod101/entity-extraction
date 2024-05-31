import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from PIL import Image
from multipage import MultiPage
from utils.auth_utils import(
    hash_plaintext_passwords,
    save_config,
    send_forgot_username_email,
    send_reset_password_email
)

from er_app import (
    home,
    subjects_of_interest,
    entity_extraction)

st.set_page_config(
    layout="wide",
    page_title="Capgemini Invent Entity Analytics & Profiling",
    page_icon=Image.open('static/imgs/favicon.ico'),
    initial_sidebar_state="auto",
  )
 
########
# Session State
########

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

########
# Auth
########

# authenticator = stauth.Authenticate(
#     st.session_state.config['credentials'],
#     st.session_state.config['cookie']['name'],
#     st.session_state.config['cookie']['key'],
#     st.session_state.config['cookie']['expiry_days'],
#     st.session_state.config['pre-authorized']
# )

# authenticator = stauth.Authenticate(
#     st.session_state.config['credentials'],
#     st.session_state.config['cookie']['name'],
#     st.session_state.config['cookie']['key'],
#     st.session_state.config['cookie']['expiry_days'],
#     st.session_state.config['azure_openai']['endpoint'],
#     st.session_state.config['azure_openai']['api_key']

# )

# name, authentication_status, username = authenticator.login('main', fields = {'Form name': 'AI Governance & Controls Login'})
# name, authentication_status, username = authenticator.login('Login','main')

########
# Button to authenticate and maintain session 
########
if st.button("Authenticate"):
    if st.session_state.config['azure_openai']['endpoint'] and st.session_state.config['azure_openai']['api_key']:
        st.success("Found both API key and Endpoint URL")
    else:
        st.error("Please add the key and endpoint to the code")


########
# App
########
# if authentication_status:
    # If the user is authenticated run app
    # app = MultiPage(authenticator, name)
app = MultiPage('main')

# Application pages
app.add_page("Home",  home.run)
app.add_page("Extract entities & relations from text",  entity_extraction.run)
app.add_page("Generate a profile a subject of interest",  subjects_of_interest.run)

# Run app
app.run_app()