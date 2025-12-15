# Task 3 transform
# join surveys with cleaned users metadata to create fct_survey_feedback

import logging
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from staging.ingestion import load_staging
from cleaned.cleaning import clean_surveys, clean_users

log = logging.getLogger(__name__)


def _rating_category(r):
    # NPS-style: 4-5 promoter, 3 passive, 1-2 detractor
    if r >= 4:
        return "Promoter"
    elif r == 3:
        return "Passive"
    return "Detractor"


def create_fact_table(surveys_df, users_df):
    log.info("Building fact table")

    # join surveys with users on email (left join keeps all surveys)
    fct_df = surveys_df.merge(users_df, on="user_email", how="left")

    # check for orphans (surveys without user match)
    orphans = fct_df["department"].isna().sum()
    if orphans:
        log.warning(f"{orphans} survey(s) without user match")

    # add useful columns
    fct_df["rating_category"] = fct_df["rating"].apply(_rating_category)
    fct_df["submission_month"] = fct_df["timestamp"].dt.to_period("M").astype(str)
    fct_df["submission_year"] = fct_df["timestamp"].dt.year
    fct_df["is_orphan"] = fct_df["department"].isna()

    # reorder columns
    cols = [
        "submission_id", "user_email",
        "timestamp", "submission_month", "submission_year",
        "rating", "rating_category", "comment_text", "region",
        "full_name", "department", "country",
        "is_orphan"
    ]
    fct_df = fct_df[cols].sort_values("timestamp", ascending=False).reset_index(drop=True)

    log.info(f"Fact table: {len(fct_df)} rows")
    return fct_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    # load and clean data
    surveys, users = load_staging()
    clean_surveys_df = clean_surveys(surveys)
    clean_users_df = clean_users(users)

    # create fct table
    fct_table = create_fact_table(clean_surveys_df, clean_users_df)
    print("== FACT TABLE ==")
    print("Rows:", len(fct_table))
    print("Columns:", list(fct_table.columns))
    print()
    print(fct_table.head())
