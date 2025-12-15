# Execute the complete data processing pipeline
import logging

from staging.ingestion import load_staging
from cleaned.cleaning import clean_surveys, clean_users
from transform.transform import create_fact_table
from aggregations.aggregations import generate_all
from config import OUTPUT_DIR


def run_pipeline():
    print("Starting pipeline....")

    # Loading staging data
    print("Loading data...")
    surveys, users = load_staging()
    print(f"   Loaded {len(surveys)} surveys, {len(users)} users")

    # Clean data
    print("Cleaning data...")
    clean_surveys_df = clean_surveys(surveys)
    clean_users_df = clean_users(users)
    print(f"  Cleaned {len(clean_surveys_df)} surveys, {len(clean_users_df)} users")

    # Create fact table
    print("Creating fact table....")
    fct_df = create_fact_table(clean_surveys_df, clean_users_df)
    print(f"  Fact table: {len(fct_df)} rows")

    # Compute and save aggregations
    print("Computing aggregations...")
    aggs = generate_all(fct_df, OUTPUT_DIR)

    print(f"  Saved to {OUTPUT_DIR}")
    print("Pipeline complete!")

    # return data for notebook use
    return {
        'surveys_raw': surveys,
        'users_raw': users,
        'surveys_clean': clean_surveys_df,
        'users_clean': clean_users_df,
        'fct': fct_df,
        'aggs': aggs
    }


if __name__ == "__main__":
    run_pipeline()
    
    