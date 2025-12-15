# Task 1 Ingestion
# Load raw CSV files into staging DataFrames

import logging
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import SURVEY_RESULTS_PATH, USER_METADATA_PATH

log = logging.getLogger(__name__)

SURVEY_EXPECTED_COLUMNS = ['submission_id', 'timestamp', 'user_email', 'rating', 'comment_text', 'region']
USER_EXPECTED_COLUMNS = ['user_email', 'full_name', 'department', 'country']


def load_survey_results(path):
    # check file exists
    if not Path(path).exists():
        raise FileNotFoundError(f"Survey file not found: {path}")

    # load survey CSV with proper dtypes
    df = pd.read_csv(path, dtype={
        "submission_id": str,
        "timestamp": str,
        "user_email": str,
        "rating": "Int64",  # nullable int
        "comment_text": str,
        "region": str,
    })

    # check expected columns exist
    missing = set(SURVEY_EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in survey file: {missing}")

    log.info(f"Loaded {len(df)} rows from {path}")
    return df


def load_user_metadata(path):
    # check file exists
    if not Path(path).exists():
        raise FileNotFoundError(f"User metadata file not found: {path}")

    # load user metadata CSV
    df = pd.read_csv(path, dtype={
        "user_email": str,
        "full_name": str,
        "department": str,
        "country": str,
    })

    # check expected columns exist
    missing = set(USER_EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in user file: {missing}")

    log.info(f"Loaded {len(df)} rows from {path}")
    return df


def load_staging():
    stg_survey_results = load_survey_results(SURVEY_RESULTS_PATH)
    stg_user_metadata = load_user_metadata(USER_METADATA_PATH)
    return stg_survey_results, stg_user_metadata


if __name__ == "__main__":
    surveys, users = load_staging()
    print("=== SURVEYS ===")
    print(surveys.head())
    print(surveys.dtypes)
    print()
    print("=== USERS ===")
    print(users.head())
