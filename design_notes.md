# Design Notes

## 1. Stack

Python + Pandas. Chose this because:
- Standard for data work, easy to extend for ML later
- No database setup needed
- Works fine for this data size (~800 rows)

Could have used DuckDB or SQLite but felt like overkill here.

## 2. Data Flow

```
Raw CSVs
    |
    v
Staging (load as-is, explicit dtypes)
    |
    v
Cleaning (validate, normalize, dedupe)
    |
    v
Transform (join surveys + users, add derived columns)
    |
    v
Aggregations (metrics to CSV)
```

## 3. Project Structure

```
src/
    config.py           # paths and constants
    pipeline.py         # runs everything, returns data dict
    staging/
        ingestion.py    # load CSVs with explicit dtypes
    cleaned/
        cleaning.py     # validation and normalization
    transform/
        transform.py    # join + derived columns
    aggregations/
        aggregations.py # compute and save metrics
    notebooks/
        exploration.ipynb
```

Each folder = one layer. Pipeline.py ties it together.

## 4. What Each Step Does

### Ingestion
Loads CSVs with explicit dtypes (Int64 for rating so nulls work). No transformations, just load.

### Cleaning

Surveys:
- Drop duplicate submission_id
- Normalize email (lowercase, trim)
- Drop nulls in email
- Drop ratings outside 1-5
- Parse timestamp, drop invalid ones
- Normalize region to uppercase

Users:
- Normalize email
- Trim department and full_name
- Missing country becomes "Unknown" (not dropped). Why? Dropping would lose the user entirely, meaning all their surveys would become orphans. Setting to "Unknown" keeps the data and makes it obvious there's a gap to fix.
- Drop duplicate emails

Added logging so you can see what gets dropped and why. In production, silent data loss is dangerous. If 50% of rows suddenly get dropped, you want to know immediately, not find out weeks later when someone asks "why are the numbers down?"

The logs show:
- How many duplicates removed
- How many invalid ratings
- How many bad timestamps
- How many missing countries (set to Unknown)

This makes debugging easier and gives visibility into data quality over time.

### Transform

Left join surveys with users on email. Keeps all surveys even if no user match (those become "orphans").

Why left join? We don't want to lose survey data just because HR hasn't added the user yet. Better to flag them as orphans and investigate later than to silently drop feedback.

Added columns:
- rating_category: Promoter (4-5), Passive (3), Detractor (1-2). This is NPS-style segmentation, useful for quick analysis like "what % are detractors?"
- submission_month: "2024-01" format. Makes it easy to group by month for trend analysis without datetime operations
- submission_year: same idea, for year-over-year comparisons
- is_orphan: True if no user match. Flags data quality issues so analysts know which rows might be incomplete

### Aggregations

Three outputs:
1. avg_rating_by_department (with count)
2. avg_rating_by_region (with count)
3. rating_distribution_by_department

All sorted by avg_rating descending, rounded to 2 decimals.

## 5. Data Quality

What we found:
- 809 surveys, 804 after cleaning (5 dropped)
- 62 users, 62 after cleaning (1 had missing country, set to Unknown)
- 2 orphan surveys (emails not in user table)

Validation happens in cleaning.py with logging:
- Duplicates: logged and dropped
- Invalid ratings: logged and dropped
- Invalid timestamps: logged and dropped
- Missing country: logged and set to "Unknown"

## 6. Scalability

Current setup works for data that fits in memory. For bigger data:

### 100x bigger (80k rows)

- Pandas still fine, just needs more memory
- Add chunked reads if memory is tight (`pd.read_csv(..., chunksize=10000)`)
- Add indexes if using a database for faster queries

### 1000x+ (millions of rows)

- **Switch to Polars or DuckDB:** Pandas is single-threaded and loads everything into memory. Polars is multi-threaded and faster. DuckDB runs SQL on files without loading them fully into memory.
- **Partition by date:** Instead of one big file, split into `surveys_2024_01.csv`, `surveys_2024_02.csv`. Query only what you need.
- **Incremental loads:** Don't reprocess everything. Only process new data since last run. Track last processed timestamp.

### Real-time (1000+ surveys/minute)

Current batch approach won't work. Need streaming architecture:

- **Kafka for ingestion:** Why? CSVs can't handle continuous data. Kafka is a message queue that buffers incoming surveys. Producers (web app, mobile app) send surveys to Kafka. Consumers read from Kafka at their own pace. If cleaning is slow, Kafka holds the data until you catch up. Also handles retries if something fails.

- **Stream processor for cleaning:** Why? Can't wait to collect a batch. Use Flink or Spark Streaming to clean each survey as it arrives. Same logic as cleaning.py but running continuously. Validates rating, normalizes email, etc. in milliseconds.

- **Write to database directly:** Why? CSVs don't support concurrent writes or real-time queries. Use PostgreSQL, BigQuery, or Snowflake. BI tools can query live data. Analysts see results within seconds of survey submission.

- **Handle late data:** Surveys might arrive out of order (network delays). Use event time (when survey was submitted) not processing time (when we received it). Watermarks tell the system "we've seen all data up to this timestamp".

## 7. Testing and Error Handling

### Unit Tests

Created `src/tests/test_cleaning.py` with pytest tests covering:

**Survey cleaning tests:**
- Drops invalid ratings (outside 1-5)
- Drops null ratings
- Normalizes email to lowercase and trims whitespace
- Normalizes region to uppercase
- Drops invalid timestamps
- Drops duplicate submission_ids (keeps first)

**User cleaning tests:**
- Missing country becomes "Unknown"
- Empty country becomes "Unknown"
- Normalizes email
- Trims department whitespace
- Drops duplicate emails (keeps first)

Run with: `pytest src/tests/ -v`

### Error Handling

Added to `ingestion.py`:
- File existence check: raises `FileNotFoundError` if CSV missing
- Column validation: raises `ValueError` if expected columns are missing
- Logging when files are loaded

This catches problems early. If someone renames a column in the source file, the pipeline fails immediately with a clear message instead of crashing later with a confusing KeyError.

### Future improvements

- Airflow DAG for scheduling daily runs
- More aggregations (weekly trends, month-over-month change)
- Type hints for better IDE support
- Config for different environments (dev/staging/prod)

**Sentiment analysis on comment_text**

The aggregations show HR has the lowest rating (3.66), but the number alone doesn't tell us *why*. The `comment_text` field contains the answer, but reading 800+ comments manually doesn't scale.

Next step: use HuggingFace Inference API with a pre-trained sentiment model like `distilbert-base-uncased-finetuned-sst-2-english` to classify each comment as positive/negative, then group by topic.

Further development: add topic extraction to group comments by theme, store `sentiment_score` in the fact table for BI filtering, and set up alerts when sentiment drops.

Benefits:
- **Actionable insights**: Instead of "HR is 3.66", we get "60% of negative HR comments mention slow ticket response" — now we know what to fix
- **Scalable**: Works whether we have 800 or 800,000 comments
- **No ML expertise needed**: Pre-trained models work out of the box, just send text via HTTP and get a score back.
