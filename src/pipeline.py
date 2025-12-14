"""
Execute the complete data processing pipeline.

This function orchestrates the entire ETL workflow, running all necessary
data extraction, transformation, and loading steps in sequence to process
the starerd case data and prepare it for analysis.
"""
from staging.ingestion import load_staging
from cleaned.cleaning import clean_surveys, clean_users
from transform.transform import create_fact_table
from aggregations.aggregations import compute_aggregation
