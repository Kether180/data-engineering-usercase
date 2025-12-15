# Task 2 Cleaning
# Handle duplicates, validate ratings(1-5) , normalize emails, parse timestamps.
import logging
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import VALID_RATING_MIN, VALID_RATING_MAX
from staging.ingestion import load_staging

log = logging.getLogger(__name__)


def clean_surveys(df):
    log.info(f"Cleaning {len(df)} survey records")
    df = df.copy()

    # removing duplicate submissions
    before = len(df)
    df = df.drop_duplicates(subset=["submission_id"], keep="first")
    if len(df) < before:
        log.warning(f"Removed {before - len(df)} duplicate(s)")

    # normalize emails(lowercase, trim whitespaces)
    df["user_email"] = df["user_email"].str.strip().str.lower()

    # find all invalid rows at once
    bad_rating = ~df["rating"].between(VALID_RATING_MIN, VALID_RATING_MAX) | df["rating"].isna()
    bad_timestamp = pd.to_datetime(df["timestamp"], errors="coerce").isna()
    bad_email = df["user_email"].isna() | (df["user_email"] == "")

    if bad_rating.sum():
        log.warning(f"{bad_rating.sum()} invalid rating(s)")
    if bad_timestamp.sum():
        log.warning(f"{bad_timestamp.sum()} invalid timestamp(s)")
    if bad_email.sum():
        log.warning(f"{bad_email.sum()} invalid email(s)")

    # keep only valid rows
    valid = ~bad_rating & ~bad_timestamp & ~bad_email
    df = df[valid].copy()

    # parse timestamp now that we know they're valid
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # normalize region
    df["region"] = df["region"].str.strip().str.upper()

    log.info(f"Clean: {len(df)} valid records")
    return df


def clean_users(df):
    log.info(f"Cleaning {len(df)} user records")
    df = df.copy()

    # normalize emails (lowercase, trim whitespaces)
    df["user_email"] = df["user_email"].str.strip().str.lower()
    # trim whitespace from names and departments
    df["department"] = df["department"].str.strip()
    df["full_name"] = df["full_name"].str.strip()

    # missing country -> Unknown (keeps the data instead of dropping)
    missing = df["country"].isna() | (df["country"].str.strip() == "")
    if missing.sum():
        log.warning(f"{missing.sum()} missing country -> 'Unknown'")
        df.loc[missing, "country"] = "Unknown"
    df["country"] = df["country"].str.strip()

    # removing duplicated users by keeping first
    before = len(df)
    df = df.drop_duplicates(subset=["user_email"], keep="first")
    if len(df) < before:
        log.warning(f"Removed {before - len(df)} duplicate email(s)")

    log.info(f"Clean: {len(df)} unique users")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    surveys, users = load_staging()
    print("Before cleaning:")
    print("Surveys:", len(surveys), "rows")
    print("Users:", len(users), "rows")

    clean_surveys_df = clean_surveys(surveys)
    clean_users_df = clean_users(users)

    print("\nAfter cleaning:")
    print("Surveys:", len(clean_surveys_df), "rows")
    print("Users:", len(clean_users_df), "rows")
