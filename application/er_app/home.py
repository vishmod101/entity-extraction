import os
import streamlit as st
from streamlit_lottie import st_lottie
from utils.app_utils import check_online, load_lottieurl


def run():
    st.markdown("""
        The application demonstrates of our entity analytics and profiling and capabilitites. It consists of a set of utilities to parse and analyse unstructured text,
        focused on identifying and extrating information about individuals and related copncepts. 

        """)

    c1, c2 = st.columns([1,1])
    with c1:
      st.markdown("""
        It includes illustrations of capabilities to:
        * Identify individuals, organisations and other entities within text
        * Generate a profile of specific individuals or entities.
        """)

    with c2:
        lottie=load_lottieurl("https://lottie.host/e5fdd9ea-6230-417c-8f3d-d540eca4e6f2/ph6LcvsleR.json")
        st_lottie(lottie, width = 500, height = 550)
        