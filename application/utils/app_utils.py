import numpy as np
import pandas as pd
import streamlit as st
import re
import json
import requests
import base64
import uuid
from streamlit_lottie import st_lottie
import spacy
import docx
import PyPDF2
import markdown
from datasets import Dataset, load_dataset, load_from_disk
from bs4 import BeautifulSoup
from urllib.request import urlopen

nlp = spacy.load("en_core_web_lg")

def check_online() -> bool:
    try:
        response = requests.get("http://www.google.com", timeout=5, verify=False)
        return True
    except requests.ConnectionError:
        return False


@st.cache_data
def load_lottieurl(url: str) -> str:
    """
    Fetches the lottie animation using the URL.
    """
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        pass


def download_button(object_to_download, download_filename, button_text):
    """
    Generates a link to download the given object_to_download.
    From: https://discuss.streamlit.io/t/a-download-button-with-custom-css/4220
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    Examples:
    --------
     download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """

    if isinstance(object_to_download, bytes):
        pass

    elif isinstance(object_to_download, pd.DataFrame):
        print('here')
        object_to_download = object_to_download.to_csv(index=False)
    # Try JSON encode for everything else
    else:
        object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()
        print(b64)
    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace("-", "")
    button_id = re.sub("\d+", "", button_uuid)

    custom_css = f""" 
         <style>
            #{button_id} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: .25rem .75rem;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = (
        custom_css
        + f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br><br>'
    )

    st.markdown(dl_link, unsafe_allow_html=True)


@st.cache_data
def convert_df(df:pd.DataFrame):
    return df.to_csv(index=False).encode('utf-8')


@st.cache_data
def convert_json(df:pd.DataFrame):
    result = df.to_json(orient="index")
    parsed = json.loads(result)
    json_string = json.dumps(parsed)
    #st.json(json_string, expanded=True)
    return json_string

def get_web_text(raw_url):
    if raw_url != "":
        page = urlopen(raw_url)
        soup = BeautifulSoup(page, "html.parser" )
        web_text = ' '.join(map(lambda p:p.text,soup.find_all('p')))

        return web_text


def get_doc_text():
    doc_text=""
    with st.subheader("Upload a document"):
        file = st.file_uploader("Upload document")
        if file:
            if file.type=='application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                doc_text = convert_docx_to_markdown(file)
            if file.type=='application/pdf':
                doc_text = convert_pdf_to_markdown(file)

    return doc_text


@st.cache_data
def convert_docx_to_markdown(input_file):
    doc = docx.Document(input_file)
    paragraphs = [p.text for p in doc.paragraphs]
    markdown_text = '\n'.join(paragraphs)

    return markdown_text


@st.cache_data
def convert_pdf_to_markdown(input_file):
    pdf_reader = PyPDF2.PdfReader(input_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
        markdown_text = markdown.markdown(text)

    return markdown_text