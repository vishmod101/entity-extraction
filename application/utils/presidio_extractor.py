"Presidio Extractor class"
from typing import List, Set, Tuple, Optional
import streamlit as st
import pandas as pd
import spacy
from presidio_analyzer import (
    RecognizerResult,
)
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


@st.cache_resource()
class presidioExtractor:
    """
    Presidio Extractor class
    """

    def __init__(self, model="en_core_web_lg"):
        """
        Initialize a presidioPredictor object
        Parameters:
            model: the spaCy model to use
        """
        self.nlp = spacy.load(model)
        self.related_entities = set()


    def get_related_entities(self, text: str, analyze_results: List[RecognizerResult]) ->  pd.DataFrame:
        """
        Exposed function to take in text and return named entities
        Parameters:
            text: the text to extract entities from
        Returns:
            entities: a list of tuples of the form (subject, object)
        """
        df = pd.DataFrame.from_records([r.to_dict() for r in analyze_results])
        df["text"] = [text[res.start : res.end] for res in analyze_results]
        self.related_entities.add(tuple(list(df.groupby(['text']).groups))) 
        
        if not df.empty:
            df_subset = df[["entity_type", "text", "start", "end", "score"]].rename(
                         {
                            "entity_type": "entity_type",
                            "text": "text",
                            "start": "start",
                            "end": "end",
                            "score": "confidence",
                        },
                        axis=1,
                    )
            df_subset["Text"] = [text[res.start : res.end] for res in analyze_results]

            analysis_explanation_df = pd.DataFrame.from_records(
                            [r.analysis_explanation.to_dict() for r in analyze_results]
            )
            df_subset = pd.concat([df_subset, analysis_explanation_df], axis=1)

            return df_subset
        else:
            pass


    def anonymize(
        self,
        text: str,
        operator: str,
        analyze_results: List[RecognizerResult],
        mask_char: Optional[str] = None,
        number_of_chars: Optional[str] = None,
        encrypt_key: Optional[str] = None,
    ):
        """Anonymize identified input using Presidio Anonymizer.
        :param text: Full text
        :param operator: Operator name
        :param mask_char: Mask char (for mask operator)
        :param number_of_chars: Number of characters to mask (for mask operator)
        :param encrypt_key: Encryption key (for encrypt operator)
        :param analyze_results: list of results from presidio analyzer engine
        """

        if operator == "mask":
            operator_config = {
                "type": "mask",
                "masking_char": mask_char,
                "chars_to_mask": number_of_chars,
                "from_end": False,
            }

        # Define operator config
        elif operator == "encrypt":
            operator_config = {"key": encrypt_key}
        elif operator == "highlight":
            operator_config = {"lambda": lambda x: x}
        else:
            operator_config = None

        # Change operator if needed as intermediate step
        if operator == "highlight":
            operator = "custom"
        elif operator == "synthesize":
            operator = "replace"
        else:
            operator = operator

        res = AnonymizerEngine().anonymize(
            text,
            analyze_results,
            operators={"DEFAULT": OperatorConfig(operator, operator_config)},
        )
        return res


    def annotate(self, text: str, analyze_results: List[RecognizerResult]):
        """Highlight the identified PII entities on the original text
           :param text: Full text
           :param analyze_results: list of results from presidio analyzer engine
         """
        tokens = []

        # Use the anonymizer to resolve overlaps
        results = self.anonymize(
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