import os
import json
import streamlit as st 
from streamlit_extras.customize_running import center_running
from streamlit_extras.capture import stdout
import pandas as pd 
from annotated_text import annotated_text
import dotenv
import streamlit.components.v1 as components
from presidio_analyzer import AnalyzerEngine
from utils.app_utils import check_online
from utils.query_executor import QueryExecutor
from utils.graph_prompts import knowledge_graph_v1
from utils.graph_utils import create_graph, create_vis


pd.options.display.max_rows = 1000
dotenv.load_dotenv()

HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem">{}</div>"""


def run():
        
    st.subheader("SoI Profiling")
    st.write("""Provide an SoI and this program will execute a custom google search to identify content related to the subject.
                It will analyse each web page and identify related entities then generate a graph of association. Note: An
                internet connection is required to run this app.
               """)

    if 'soi' not in st.session_state:
        st.session_state['soi'] = ''

    placeholder = st.empty()

    with placeholder.container():

        model_list = [
            "spaCy/en_core_web_lg",
            "flair/ner-english-large",
            "HuggingFace/obi/deid_roberta_i2b2",
            "HuggingFace/StanfordAIMI/stanford-deidentifier-base",
            "stanza/en"
            ]

        # Select model
        with st.sidebar:
            st_model = st.sidebar.selectbox(
                'Select NLP Engine',
                label_visibility="collapsed",            
                options=model_list,
                index=0
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
        args["google_engine_id"] = os.getenv("GOOGLE_CUSTOM_SEARCH_ID")
        args["custom_search_key"] = os.getenv("GOOGLE_CUSTOM_SEARCH_KEY")
        args["model_package"] = st_model_package
        args["model"] = st_model
        args["https_flag"] = True

       
        with st.sidebar:
            genAnalyzer = AnalyzerEngine()
            st_entities = st.sidebar.multiselect(
                label='Define the entity types to extract',
                label_visibility="collapsed",
                options=genAnalyzer.get_supported_entities(),
                default=['PERSON'],        
                help="Limit the list of entities detected.")
        args["entities"] = st_entities

        with st.sidebar:
            st_min_relations = st.sidebar.slider(
               label='Set the minimum number of relationships to find for an SoI',
               label_visibility="collapsed",
               min_value=1,
               max_value=500,
               value=50,
               help="Set how many relationships to other entities you want to find. More relationships means a longer search duration",
        )
        args["k"] = st_min_relations

        st.markdown("**Define subjects(s) of interest**")
 
        soi=""

        online = check_online()
        if not online:
            st.warning("You are not online. An internet connection is required to run this app.")
        else:
            soi = st.text_input("Enter Subject of Interest", value="")

        if st.button('Search'):

            st.markdown("**SoI Search**")
            with st.expander("View logs"):
                output = st.empty()
                with stdout(output.code, terminator=""):
                    print(f"Params: {args}")
                    args["q"] = soi
                    executor = QueryExecutor(args)
                    st.session_state['soi'] = soi

                    iterate_further = True
                    iterations = 0

                    res = []
                    txt = []
 
                    while iterate_further:
                        # Get the top 10 results for the current query
                        results = executor.getQueryResult(executor.q, 10, executor.https_flag)
                        print(results)
                        print(f"=========== Iteration: {iterations} - Query: {executor.q} ===========")
                        for i, item in enumerate(results):
                            print(f"URL ( {i+1} / 10): {item['link']}")
                            text =  executor.processText(item['link'])
                            if text:
                                txt.append(text)
                                analyze_results = executor.model.analyzer.analyze(
                                    text=text, 
                                    entities=executor.model.entities,
                                    language="en",
                                    return_decision_process=True
                                )
                                df = executor.extractor.get_related_entities(text=text,
                                                                             analyze_results=analyze_results)
                                res.append(df)
                            if not executor.checkContinue() and iterations > 50:
                                iterate_further = False
                                break
                            iterations += 1
                            # If a new iteration is needed, get the new query
                        if not executor.getNewQuery():
                            print( "No new queries to try")
                            print( "Exiting ...")
                            break

                    print(f"Total # of iterations = {iterations}")

                    resdf = pd.concat(res)
                    ents = list(resdf["Text"])
                    ents = [e.split('.')[0] for e in ents]

                    ent_set = set(ents)
                    un_ent_lst = list(ent_set)

            st.markdown("**Extracted Entities**")
            st.dataframe(resdf.reset_index(drop=True), use_container_width=True)

            plain_text = ' '.join(txt)

            analyze_txt = executor.model.analyzer.analyze(
                text=plain_text, 
                language="en",
                entities=executor.model.entities,
                return_decision_process=True
            )

            annotated_tokens = executor.extractor.annotate(text=plain_text, analyze_results=analyze_txt)
            with st.expander("View extracted text"):
               at = annotated_text(*annotated_tokens)
               st.write(at)

            #######
            # Entity coreference resolution
            #######
            ''' ToDo '''

            #######
            # Create knowledge graph
            #######
            with st.spinner(text="Creating association graph...🤓"):

                text = plain_text[:16385]
                kg = knowledge_graph_v1(un_ent_lst, text)
  
                jsonstruct = json.loads(kg)
                print(jsonstruct)
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

