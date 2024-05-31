import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import utils.css_utils as cutl

# Define the multipage class to manage the multiple apps in our program 
class MultiPage: 
    """Framework for combining multiple streamlit applications."""

    # def __init__(self, authenticator, name) -> None:
    #     """Constructor class to generate a list which will store all our applications as an instance variable."""
    #     self.pages = []
    #     self.authenticator = authenticator
    #     self.user = name

    def __init__(self, name) -> None:
        """Constructor class to generate a list which will store all our applications as an instance variable."""
        self.pages = []
        self.user = name    

    
    def add_page(self, title, func) -> None: 
        """Class Method to add pages to the project
        Args:
            title ([str]): The title of page which we are adding to the list of apps 
            func: Python function to render this page in Streamlit
        """

        self.pages.append(
            {
                "title": title, 
                "function": func
            }
        )


    def run_app(self, *args):
        """Adds a 'Navigation' Selectbox to the sidebar from which
        the added apps can be selected and runs the actually selected
        application within the main app. Optional args can be passed.
        """
        
        cutl.stNotification(f'Logged in as {self.user}')
        
        st.title("Entity Analytics & Profiling")

        cutl.local_css("static/css/streamlit.css")
        logo = Image.open("static/imgs/DES_logo_2016_White_RGB.png")
        st.sidebar.image(logo, width=250)

        app = st.sidebar.selectbox(
            "Select option", self.pages, label_visibility="collapsed", format_func=lambda page: page["title"]
        )

        app["function"](*args)

        