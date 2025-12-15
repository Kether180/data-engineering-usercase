# Task 4 Aggregations
# compute metrics from fact table and save to CSV
import logging
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import OUTPUT_DIR
from staging.ingestion import load_staging
from cleaned.cleaning import clean_surveys, clean_users
from transform.transform import create_fact_table

log = logging.getLogger(__name__)


def avg_rating_by_department(fct_df):
    # avg rating per department with count
    return (
        fct_df.groupby(fct_df['department'].fillna('Unknown'))
        .agg(avg_rating=('rating', 'mean'), count=('rating', 'count'))
        .round({'avg_rating': 2})
        .reset_index()
        .sort_values('avg_rating', ascending=False)
    )


def avg_rating_by_region(fct_df):
    # avg rating per region with count
    return (
        fct_df.groupby('region')
        .agg(avg_rating=('rating', 'mean'), count=('rating', 'count'))
        .round({'avg_rating': 2})
        .reset_index()
        .sort_values('avg_rating', ascending=False)
    )


def rating_distribution_by_department(fct_df):
    # count of each rating (1-5) per department
    return (
        fct_df.groupby([fct_df['department'].fillna('Unknown'), 'rating'])
        .size()
        .reset_index(name='rating_count')
        .sort_values(['department', 'rating'])
    )


def generate_all(fct_df, output_dir):
    # generate all aggregations and save to CSV
    log.info("Generating aggregations")
    output_dir.mkdir(exist_ok=True)

    aggs = {
        'avg_rating_by_department': avg_rating_by_department(fct_df),
        'avg_rating_by_region': avg_rating_by_region(fct_df),
        'rating_distribution_by_department': rating_distribution_by_department(fct_df),
    }

    for name, df in aggs.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        log.info(f"Saved {name}.csv")

    return aggs


def print_results(aggs):
    # print summary to console
    print("\n" + "=" * 55)
    print("RESULTS")
    print("=" * 55)

    print("\nAvg Rating by Department:")
    print("-" * 35)
    for _, r in aggs['avg_rating_by_department'].iterrows():
        print(f"  {r['department']:<20} {r['avg_rating']:.2f} (n={r['count']})")

    print("\nAvg Rating by Region:")
    print("-" * 35)
    for _, r in aggs['avg_rating_by_region'].iterrows():
        print(f"  {r['region']:<10} {r['avg_rating']:.2f} (n={r['count']})")

    print("\nRating Distribution:")
    print("-" * 35)
    pivot = (
        aggs['rating_distribution_by_department']
        .pivot(index='department', columns='rating', values='rating_count')
        .fillna(0).astype(int)
    )
    print(pivot.to_string())
    print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    # build fact table
    surveys, users = load_staging()
    clean_surveys_df = clean_surveys(surveys)
    clean_users_df = clean_users(users)
    fct_df = create_fact_table(clean_surveys_df, clean_users_df)

    # compute and save aggregations
    aggs = generate_all(fct_df, OUTPUT_DIR)
    print_results(aggs)
    