"""
Query Executor class and methods
"""
# import pprint
import os
import re
from typing import Dict, List, Optional, Tuple
import requests
import streamlit as st
from bs4 import BeautifulSoup
from itertools import chain
from googleapiclient.discovery import build
from utils.presidio import Presidio
from utils.presidio_extractor import presidioExtractor
from utils.app_utils import check_online


@st.cache_resource
class QueryExecutor:
    "Creates a QueryExecutor object" 

    def __init__(self, args) -> None:
        """
        Initialize a QueryExecutor object
        Instance Variables:
            query: the query string
            k: the number of tuples that we request in the output
            google_engine_id: the Google Custom Search Engine ID
            engine: the Google Custom Search Engine
            seen_urls: the set of URLs that we have already seen
            used_queries: the set of queries that we have already used
            extractor: the extractor object 
        """
        self.q = args["q"]
        self.k = args["k"]
        self.custom_search_key = args["custom_search_key"]
        self.google_engine_id = args["google_engine_id"]
        self.https_flag = args["https_flag"]
        self.engine = build("customsearch", "v1", developerKey=args["custom_search_key"])
        self.seen_urls = set()
        self.used_queries = set([self.q])
        self.model = Presidio(args["model_package"], args["model"], args["entities"])
        self.extractor = presidioExtractor()


    def getQueryResult(self, query: str, k, https_flag: bool) -> List:
        """
        Get the top 10 results for a given query from Google Custom Search API
        Source: https://github.com/googleapis/google-api-python-client/blob/main/samples/customsearch/main.py
        """
        if https_flag:
            full_res = (
                self.engine.cse()
                .list(
                    q=query,
                    cx=self.google_engine_id,
                )
                .execute()
            )
            return full_res["items"][0 : k + 1]
        else:
            url = f"https://www.googleapis.com/customsearch/v1?key={self.custom_search_key}&cx={self.google_engine_id}&q={query}"
            full_res = requests.get(url, verify=False).json()
            return full_res["items"][0 : k + 1]


    def processText(self, url: str) -> Optional[str]:
        """
        Get the tokens from a given URL
        If webpage retrieval fails (e.g. because of a timeout), it is skipped (None returned)

        Extracts the plain text from the URL using Beautiful Soup.
        If the resulting plain text is longer than 10,000 characters, it is truncated.
        Only the text in the <p> tags is processed.

        Parameters:
            url (str) - the URL to process
        Returns:
            List[str] - the list of tokens
        """

        try:
            print("        Fetching text from url ...")
            page = requests.get(url, timeout=5, verify=self.https_flag)
        except requests.exceptions.Timeout:
            print(f"Error processing {url}: The request timed out. Moving on...")
            return None
        try:
            soup = BeautifulSoup(page.content, "html.parser")
            html_blocks = soup.find_all("p")
            text = ""
            for block in html_blocks:
                text += block.get_text()

            if text != "":
                text_len = len(text)
                print(
                    f"        Trimming webpage content from {text_len} to 10000 characters"
                )
                preprocessed_text = (text[:10000]) if text_len > 10000 else text
                print(
                    f"        Webpage length (num characters): {len(preprocessed_text)}"
                )
                # Removing redundant newlines and some whitespace characters.
                preprocessed_text = re.sub("\t+", " ", preprocessed_text)
                preprocessed_text = re.sub("\n+", " ", preprocessed_text)
                preprocessed_text = re.sub(" +", " ", preprocessed_text)
                preprocessed_text = preprocessed_text.replace("\u200b", "")

                return preprocessed_text
            else:
                return None
        except Exception as e:
            print(f"Error processing {url}: {e}. Moving on ...")
            return None


    def parseResult(self, result: Dict[str, str]) -> None:
        """
        Parse the result of a query.
        Exposed function for use by main function.
        Parameters:
            result (dict) - one item as returned as the result of a query
        Returns:
            None
        """
        url = result["link"]
        if url not in self.seen_urls:
            self.seen_urls.add(url)
            text = self.processText(url)
            if not text:
                return None
        return text


    def checkContinue(self) -> bool:
        """
        Evaluate if we have evaluated at least k tuples, ie continue or halt.
        Parameters: None
        Returns: bool (True if we need to find more relations, else False)
        """
        lst = list(chain.from_iterable(self.extractor.related_entities))
        ent_count = len(set(lst))
        print(f"entity count: {ent_count}")
        return ent_count < self.k

 
    def getNewQuery(self) -> Optional[str]:
        """
        Creates a new query.
        Select from X a tuple y such that y has not been used for querying yet
        Create a query q from tuple y by concatenating
        the attribute values together.
        If no such y tuple exists, then stop/return None.
        (ISE has "stalled" before retrieving k high-confidence tuples.)

        Parameters:
            None
        Returns:
            query (str) if available; else None
        """
        # Iterating through extracted tuples
        for relation in list(self.extractor.related_entities):
            tmp_query = " ".join(relation)
            # Checking if query has been used
            if tmp_query not in self.used_queries:
                # Adding query to used queries
                self.used_queries.add(relation)
                # Setting new query
                self.q = tmp_query
                return self.q
            # No valid query found
            return None
