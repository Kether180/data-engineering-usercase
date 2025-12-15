# Tests for cleaning functions
import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from cleaned.cleaning import clean_surveys, clean_users


class TestCleanSurveys:

    def test_drops_invalid_rating(self):
        df = pd.DataFrame({
            'submission_id': ['1', '2', '3'],
            'timestamp': ['2024-01-01T10:00:00', '2024-01-01T11:00:00', '2024-01-01T12:00:00'],
            'user_email': ['a@test.com', 'b@test.com', 'c@test.com'],
            'rating': [3, 6, 0],  # 6 and 0 are invalid
            'comment_text': ['ok', 'bad', 'bad'],
            'region': ['EMEA', 'APAC', 'EMEA']
        })
        result = clean_surveys(df)
        assert len(result) == 1
        assert result.iloc[0]['rating'] == 3

    def test_drops_null_rating(self):
        df = pd.DataFrame({
            'submission_id': ['1', '2'],
            'timestamp': ['2024-01-01T10:00:00', '2024-01-01T11:00:00'],
            'user_email': ['a@test.com', 'b@test.com'],
            'rating': [4, None],
            'comment_text': ['good', 'missing'],
            'region': ['EMEA', 'APAC']
        })
        result = clean_surveys(df)
        assert len(result) == 1

    def test_normalizes_email(self):
        df = pd.DataFrame({
            'submission_id': ['1'],
            'timestamp': ['2024-01-01T10:00:00'],
            'user_email': ['  Test@Email.COM  '],
            'rating': [4],
            'comment_text': ['good'],
            'region': ['EMEA']
        })
        result = clean_surveys(df)
        assert result.iloc[0]['user_email'] == 'test@email.com'

    def test_normalizes_region_to_uppercase(self):
        df = pd.DataFrame({
            'submission_id': ['1'],
            'timestamp': ['2024-01-01T10:00:00'],
            'user_email': ['a@test.com'],
            'rating': [4],
            'comment_text': ['good'],
            'region': ['  emea  ']
        })
        result = clean_surveys(df)
        assert result.iloc[0]['region'] == 'EMEA'

    def test_drops_invalid_timestamp(self):
        df = pd.DataFrame({
            'submission_id': ['1', '2'],
            'timestamp': ['2024-01-01T10:00:00', 'not-a-date'],
            'user_email': ['a@test.com', 'b@test.com'],
            'rating': [4, 5],
            'comment_text': ['good', 'great'],
            'region': ['EMEA', 'APAC']
        })
        result = clean_surveys(df)
        assert len(result) == 1

    def test_drops_duplicate_submission_id(self):
        df = pd.DataFrame({
            'submission_id': ['1', '1', '2'],
            'timestamp': ['2024-01-01T10:00:00', '2024-01-01T11:00:00', '2024-01-01T12:00:00'],
            'user_email': ['a@test.com', 'a@test.com', 'b@test.com'],
            'rating': [4, 5, 3],
            'comment_text': ['first', 'duplicate', 'other'],
            'region': ['EMEA', 'EMEA', 'APAC']
        })
        result = clean_surveys(df)
        assert len(result) == 2
        assert result[result['submission_id'] == '1'].iloc[0]['rating'] == 4  # keeps first


class TestCleanUsers:

    def test_missing_country_becomes_unknown(self):
        df = pd.DataFrame({
            'user_email': ['a@test.com'],
            'full_name': ['Test User'],
            'department': ['Engineering'],
            'country': [None]
        })
        result = clean_users(df)
        assert result.iloc[0]['country'] == 'Unknown'

    def test_empty_country_becomes_unknown(self):
        df = pd.DataFrame({
            'user_email': ['a@test.com'],
            'full_name': ['Test User'],
            'department': ['Engineering'],
            'country': ['   ']
        })
        result = clean_users(df)
        assert result.iloc[0]['country'] == 'Unknown'

    def test_normalizes_email(self):
        df = pd.DataFrame({
            'user_email': ['  TEST@Email.COM  '],
            'full_name': ['Test User'],
            'department': ['Engineering'],
            'country': ['USA']
        })
        result = clean_users(df)
        assert result.iloc[0]['user_email'] == 'test@email.com'

    def test_trims_department(self):
        df = pd.DataFrame({
            'user_email': ['a@test.com'],
            'full_name': ['Test User'],
            'department': ['  Engineering  '],
            'country': ['USA']
        })
        result = clean_users(df)
        assert result.iloc[0]['department'] == 'Engineering'

    def test_drops_duplicate_emails(self):
        df = pd.DataFrame({
            'user_email': ['a@test.com', 'a@test.com', 'b@test.com'],
            'full_name': ['User One', 'User One Dup', 'User Two'],
            'department': ['Engineering', 'Sales', 'Marketing'],
            'country': ['USA', 'UK', 'Germany']
        })
        result = clean_users(df)
        assert len(result) == 2
        assert result[result['user_email'] == 'a@test.com'].iloc[0]['department'] == 'Engineering'
