# Configuration file for the Survey Feedback Pipeline

from pathlib import Path

# -> PATHS
# Base directory (root)

BASE_DIR = Path(__file__).parent.parent

# Input data paths

DATA_DIR = BASE_DIR / "data"
SURVEY_RESULTS_PATH = DATA_DIR / "survey_results.csv"
USER_METADATA_PATH = DATA_DIR / "user_metadata.csv"

# Output paths

OUTPUT_DIR = BASE_DIR / "aggregations"

# -> CONSTANTS

# Validation rules

VALID_RATING_MIN = 1
VALID_RATING_MAX = 5
