import time
import json
import pandas as pd
import streamlit as st 
import streamlit.components.v1 as components
from presidio_analyzer import AnalyzerEngine
from annotated_text import annotated_text
from utils.query_executor import QueryExecutor
from utils.graph_prompts import knowledge_graph_v1
from utils.app_utils import get_doc_text, get_web_text, check_online
from utils.graph_utils import create_graph, create_vis


HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem">{}</div>"""

def run():

    if "reset" not in st.session_state:
        st.session_state.reset = False

    st.subheader("Entity Extraction")
    st.write("""This program will parse a set of documents or web page and identify any individuals within it. The full text will be returned with annotations 
                highlighting identified individuals. Note: An internet connection is required to run this app.
             """)

    model_help_text = """
        Select which Named Entity Recognition (NER) model to use for entity detection, in parallel to rule-based recognizers.
        Presidio supports multiple NER packages off-the-shelf, such as spaCy, Huggingface, Stanza and Flair,
        as well as service such as Azure Text Analytics.
        """

    model_list = [
            "spaCy/en_core_web_lg",
            "flair/ner-english-large",
            "HuggingFace/obi/deid_roberta_i2b2",
            "HuggingFace/StanfordAIMI/stanford-deidentifier-base",
            "stanza/en",
            ]

    # Select model
    st_model = st.sidebar.selectbox(
        'Select NLP Engine',
        label_visibility="collapsed",
        options=model_list,
        index=0,
        help=model_help_text,
    )

    # Extract model package.
    st_model_package = st_model.split("/")[0]

    # Remove package prefix (if needed)
    st_model = (
            st_model
            if st_model_package.lower() not in ("spacy", "stanza", "huggingface")
            else "/".join(st_model.split("/")[1:])
        )

    args = {}
    args["google_engine_id"] = ""
    args["custom_search_key"] = ""
    args["model_package"] = st_model_package
    args["model"] = st_model
    args["q"] = ""
    args["k"] = 5
    args["https_flag"] = True

    genAnalyzer = AnalyzerEngine()

    with st.sidebar:
        st_entities = st.sidebar.multiselect(
            label='Define the entity types to extract',
            label_visibility="collapsed",
            options=genAnalyzer.get_supported_entities(),
            default=['PERSON'],        
            help="Limit the list of entities detected. " 
                 "This list is dynamic and based on the NER model and registered recognizers. "
        )
        args["entities"] = st_entities
        st_threshold = st.sidebar.slider(
            label='Acceptance threshold',
            label_visibility="collapsed",
            min_value=0.0,
            max_value=1.0,
            value=0.35,
            help="Define the threshold for accepting a detection.",
        )

    online = check_online()
    if not online:
        st.warning("You are not online. An internet connection is required to run this app.")
    else:
        source_text_options = ["document", "web page"]
        source_text = st.radio("Select input text source", source_text_options, horizontal=True)

    if 'plain_text' not in st.session_state:
        st.session_state['plain_text'] = ''
    if 'analyzed_text' not in st.session_state:
        st.session_state['analyzed_text'] = ''

    plain_text=""

    online = check_online()
    if not online:
        st.warning("You are not online. An internet connection is required to run this app.")
    else:
        if source_text == 'document':
            plain_text = get_doc_text()
        if source_text == 'web page':
            raw_url = st.text_input("Enter URL:","")
            plain_text = get_web_text(raw_url)
            

    if plain_text != "":
        st.session_state['plain_text'] = plain_text
               
        if st.button('Extract Entities'):

            # Choose entities
            executor = QueryExecutor(args)
 
            st_analyze_results = executor.model.analyzer.analyze(
                text=plain_text,
                entities=st_entities,
                language="en",
                score_threshold=st_threshold,
                return_decision_process=True
            )

            annotated_tokens = executor.extractor.annotate(text=plain_text, analyze_results=st_analyze_results)
            df = executor.extractor.get_related_entities(text=plain_text,
                                                         analyze_results=st_analyze_results)

            ents = list(df["Text"])
            ents = [e.split('.')[0] for e in ents]
            ent_set = set(ents)
            un_ent_lst = list(ent_set)

            st.markdown("**Extracted Entities**")
            st.dataframe(df.reset_index(drop=True), use_container_width=True)

            with st.expander("View extracted text"):
                at = annotated_text(*annotated_tokens)
                st.write(at)

            #######
            # Create knowledge graph
            #######
            with st.spinner(text="Creating association graph...🤓"):

                text = plain_text[:16385]
                kg = knowledge_graph_v1(un_ent_lst, text)
                
                jsonstruct = json.loads(kg)
                gdf = pd.DataFrame(jsonstruct['graph'])
                g = create_graph(gdf)

                st.markdown("**Graph of associated entities and concepts**")
                create_vis(g, 'knowledge_graph')
                HtmlFile = open("knowledge_graph.html", 'r', encoding='utf-8')
                source_code = HtmlFile.read()
                components.html(source_code, height = 1200,width=1600)

            # Reset button
            if st.button("Reset"):
                st.session_state.reset = True 
                st.rerun()
            else:
                st.session_state.reset = False
