# Design Notes: Survey Feedback Pipeline

## 1. Tools and Stack

**Chosen stack:** Python + Pandas

**Why this choice:**
- Pandas is the standard tool for data manipulation in ML/AI workflows
- Works well with downstream ML libraries (scikit-learn, PyTorch, etc.)
- No database setup required, runs anywhere Python is installed
- Good balance between simplicity and functionality for this data size (~800 rows)
- Easy to extend if we need to add feature engineering or model training later

**Alternatives considered:**
- DuckDB + SQL: Great for larger datasets, but overkill for this size
- dbt: Better suited for warehouse environments with existing SQL infrastructure
- Pure SQL (SQLite): Would work, but less flexible for complex transformations

## 2. High-Level Data Flow

```
[Raw CSVs]
    |
    v
[Staging Layer] -----> stg_survey_results, stg_user_metadata
    |                  (loaded as-is, no changes)
    |
    v
[Cleaning Layer] ----> clean_survey_results, clean_user_metadata
    |                  (validated, normalized, deduplicated)
    |
    v
[Transform Layer] ---> fct_survey_feedback
    |                  (joined, enriched, analytics-ready)
    |
    v
[Aggregations] ------> CSV exports in /aggregations folder
                       (business metrics)
```

**The boundary between raw and clean is explicit:**
- Staging = data loaded into memory, untouched
- Cleaned = transformations applied, data validated

## 3. Project Structure

```
src/
    config.py                   (Paths, constants, settings)
    pipeline.py                 (Main orchestrator, runs all steps)
    |
    +-- staging/
    |       ingestion.py        (Task 1: Load CSVs into staging DataFrames)
    |
    +-- cleaned/
    |       cleaning.py         (Task 2: Validate and standardize data)
    |
    +-- transform/
    |       transform.py        (Task 3: Join tables, create fact table)
    |
    +-- aggregations/
    |       aggregations.py     (Task 4: Compute metrics, export CSVs)
    |
    +-- notebooks/
            exploration.ipynb   (Ad-hoc analysis and visualization)
```

**Why this structure:**
- Each folder represents one layer in the data flow
- Separation of concerns: each file does one thing
- Easy to test individual components
- Clear naming: stg_ for staging, clean_ for cleaned, fct_ for fact tables
- Pipeline.py ties everything together and can be run as a single command

## 4. Transformation Logic

(To be filled in as we implement each task)

### 4.1 Ingestion
...

### 4.2 Cleaning
...

### 4.3 Join and Fact Table
...

### 4.4 Aggregations
...

## 5. Data Quality and Validation

(To be filled in after implementation)

## 6. Scalability Considerations

(To be filled in after implementation)

## 7. If I Had More Time

(To be filled in after implementation)
