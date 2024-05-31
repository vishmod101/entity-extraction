from splink.duckdb.linker import DuckDBLinker
from splink.duckdb.blocking_rule_library import block_on
import splink.duckdb.comparison_library as cl
import splink.duckdb.comparison_template_library as ctl
import streamlit as st


@st.cache_resource
def run_entity_resolution(input_file_a, input_file_b):
    # Blocking Rules
    blocking_settings = {
        "link_type": "link_and_dedupe",
        "blocking_rules_to_generate_predictions": [
            block_on("first_name"),
            block_on("surname"),
        ],
        "retain_intermediate_calculation_columns": True,
        "retain_matching_columns" : True,
        "comparisons": [
            ctl.name_comparison("first_name"),
            ctl.name_comparison("surname"),
            ctl.date_comparison("dob", cast_strings_to_date=True),
            cl.exact_match("city", term_frequency_adjustments=True),
            ctl.email_comparison("email", include_username_fuzzy_level=False),
        ],
    }

    linker = DuckDBLinker([input_file_a, input_file_b], blocking_settings, input_table_aliases=['data_set_1', 'data_set_2'])

    # Deterministic Rules
    deterministic_rules = [
        "l.first_name = r.first_name and levenshtein(r.dob, l.dob) <= 1",
        "l.surname = r.surname and levenshtein(r.dob, l.dob) <= 1",
        "l.first_name = r.first_name and levenshtein(r.surname, l.surname) <= 2",
        "l.email = r.email"
    ]

    # Estimate Probability of Two Random Records Match
    linker.estimate_probability_two_random_records_match(deterministic_rules, recall=0.7)

    # Estimate Parameters using Expectation Maximization
    linker.estimate_u_using_random_sampling(max_pairs=1e6, seed=1)
    linker.estimate_parameters_using_expectation_maximisation(block_on("dob"))
    linker.estimate_parameters_using_expectation_maximisation(block_on("email"))
    linker.estimate_parameters_using_expectation_maximisation(block_on("first_name"))

    # Predict and Get Results
    df_predict = linker.predict(threshold_match_probability=0.9)


    return df_predict, linker
