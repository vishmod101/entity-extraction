import os
import streamlit as st 
import pandas  as  pd
from splink.datasets import splink_datasets
from splink.duckdb.linker import DuckDBLinker
from splink.duckdb.blocking_rule_library import block_on
import splink.duckdb.comparison_template_library as ctl
import splink.duckdb.comparison_library as cl
import streamlit.components.v1 as components
from altair_saver import save
from utils.entity_resolution_utils import run_entity_resolution

HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem">{}</div>"""


def run():
    st.subheader("Entity Recognition with Splink")
    st.write("""In the expectation that a common challenge you face is the indentification and management of many datasets of different formats which originate from disparate sources, this page illustrates an example of how it might be achieved by linking two datasets of individuals from differnt sources to derive a single record for each person by linking datasets. It leverages [Splink](https://moj-analytical-services.github.io/splink/), a 'fast, accurate and scalable probabilistic data linkage' library developed by MoJ Analytical Services.  
 
Probablistic record linkage is a technique used to link together records that lack unique identifiers. In the absence of a unique identifier such as a National Insurance number, we can use a combination of individually non-unique variables such as name, gender and date of birth to identify individuals. Record linkage can be done within datasets (deduplication), between datasets (linkage), or both. Linkage is 'probabilistic' in the sense that it subject to uncertainty and relies on the balance of evidence. For instance, in a large dataset, observing that two records match on the full name John Smith provides some evidence that these two records may refer to the same person, but this evidence is inconclusive because it's possible there are two different John Smiths.  
             """)

    placeholder = st.empty()

    # Initialize df_left and df_right outside the if block
    df_left = None
    df_right = None

    with placeholder.container():
        st.subheader("*Upload two files*")
        uploaded_files = st.file_uploader('Upload your csv files',
                                        accept_multiple_files=True, type=['csv'])

    if uploaded_files is not None:  
        if len(uploaded_files) == 2:
            df_left = pd.read_csv(uploaded_files[0])
            df_right = pd.read_csv(uploaded_files[1])

            # Display the uploaded dataframes
            c1, c2 = st.columns([1,1])

            with c1:
                st.subheader("Input file A:")
                st.write("A dataset containing records relating to individuals")
                st.dataframe(df_left)

            with c2:
                st.subheader("Input file B:")
                st.write("A second dataset containing records relating to potenially the same individuals but with different keys")
                st.dataframe(df_right)

            # Execute Splink logic
            if st.button("Execute Splink Logic"):
                st.write("Splink predicts which rows link and clusters them together to produce an consolidated list of unique individuals.")
                df_predict, linker = run_entity_resolution(df_left, df_right)
                results_df = df_predict.as_pandas_dataframe(limit=10)

                with st.expander("Data profile"):
                    st.altair_chart(linker.profile_columns())

                c1, c2 = st.columns([1,1])

                with c1:
                    cc = linker.completeness_chart(cols=["first_name", "surname", "dob", "city", "email"])
                    save(cc, "completeness_chart.html",  overwrite=True) 
                    HtmlFile = open("completeness_chart.html", 'r', encoding='utf-8')
                    src = HtmlFile.read() 
                    components.html(src, width=500, height=300, scrolling=False)

                with c2:
                    st.altair_chart(linker.missingness_chart())

                st.subheader("Linked records with probabilities")
                st.dataframe(results_df)


                st.subheader("Inspect the strength of the match and the contributory factors")
                c1, c2, c3 = st.columns([0.5,1,0.5])

                with c2: 
                    df_e = df_predict.as_pandas_dataframe()
                    records_to_plot = df_e.to_dict(orient="records")

                    wc = linker.waterfall_chart(records_to_plot, filter_nulls=False)
                    save(wc, "waterfall_chart.html",  overwrite=True) 
                    HtmlFile = open("waterfall_chart.html", 'r', encoding='utf-8')
                    src = HtmlFile.read() 
                    components.html(src, width=800, height=800, scrolling=False)

        else:
            st.warning("Please upload exactly two CSV files.")
    else:
        # Handle the case when no files are uploaded
        st.info("Upload two CSV files to get started.")
