"Presidio  class"
import streamlit as st
from typing import List, Set, Tuple, Optional
from presidio_analyzer import (
    AnalyzerEngine,
    RecognizerResult,
    RecognizerRegistry,
    PatternRecognizer,
    Pattern,
)
from presidio_analyzer.nlp_engine import NlpEngine
from presidio_analyzer import RecognizerRegistry
from presidio_analyzer.nlp_engine import (
    NlpEngine,
    NlpEngineProvider,
)
from utils.presidio_utils import select_nlp_engine_and_registry

@st.cache_resource()
class Presidio:
    """
    Presidio class
    """
    def __init__(self, model_package, model_name, entities):
        """
        Initialize a presidioPredictor object
        Parameters:
            model: the spaCy model to use
        """
        self.model_package = model_package
        self.model = model_name
        self.nlp_engine, self.registry = select_nlp_engine_and_registry(model_package, model_name)
        self.analyzer = AnalyzerEngine(nlp_engine=self.nlp_engine, registry=self.registry)
        self.entities = entities

    def annotate(self, text: str, analyze_results: List[RecognizerResult]):
        """Highlight the identified PII entities on the original text
        :param text: Full text
        :param analyze_results: list of results from presidio analyzer engine
        """
        tokens = []

        # Use the anonymizer to resolve overlaps
        results = self.extractor.anonymize(
            text=text,
            operator="highlight",
            analyze_results=analyze_results,
        )

        # sort by start index
        results = sorted(results.items, key=lambda x: x.start)
        for i, res in enumerate(results):
            if i == 0:
                tokens.append(text[: res.start])

            # append entity text and entity type
            tokens.append((text[res.start : res.end], res.entity_type))

            # if another entity coming i.e. we're not at the last results element, add text up to next entity
            if i != len(results) - 1:
                tokens.append(text[res.end : results[i + 1].start])
            # if no more entities coming, add all remaining text
            else:
                tokens.append(text[res.end :])
        return tokens

    def create_ad_hoc_deny_list_recognizer(
        deny_list=Optional[List[str]],
    ) -> Optional[PatternRecognizer]:
        if not deny_list:
            return None

        deny_list_recognizer = PatternRecognizer(
            supported_entity="GENERIC_PII", deny_list=deny_list
        )
        return deny_list_recognizer

    def create_ad_hoc_regex_recognizer(
        regex: str, entity_type: str, score: float, context: Optional[List[str]] = None
    ) -> Optional[PatternRecognizer]:
        if not regex:
            return None
        pattern = Pattern(name="Regex pattern", regex=regex, score=score)
        regex_recognizer = PatternRecognizer(
              supported_entity=entity_type, patterns=[pattern], context=context
        )
        return regex_recognizer