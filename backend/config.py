"""
Configuration module for NextPlay backend.

Centralizes all configuration constants, file paths, and settings
to ensure consistency across the application.
"""

from pathlib import Path
from typing import List

# Base directory for the backend
BASE_DIR = Path(__file__).parent

# Training data paths (for data processing scripts, not required in production)
TRAINING_DATA_DIR = BASE_DIR / "training_data"
TRAINING_DATA_DATA_DIR = TRAINING_DATA_DIR / "data"
TRAINING_DATA_MAN_DIR = TRAINING_DATA_DIR / "man"
RDA_FILE = TRAINING_DATA_DATA_DIR / "gcdg_nld_smocc.rda"
DOC_FILE = TRAINING_DATA_MAN_DIR / "gcdg_nld_smocc.Rd"

# Model/data file paths (used in production, generated from training data)
MODELS_DIR = BASE_DIR / "models"
PROCESSED_CSV = MODELS_DIR / "processed_milestones.csv"
MASTERY_AGES_JSON = MODELS_DIR / "mastery_ages.json"
TRANSITION_MATRIX_JSON = MODELS_DIR / "transition_matrix.json"
MILESTONE_MAP_JSON = MODELS_DIR / "milestone_map.json"
ACTIVITIES_JSON = MODELS_DIR / "activities.json"

# Environment variable names
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_OPENAI_MODEL = "OPENAI_MODEL"

# Default OpenAI model
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

# CORS Configuration
# Base allowed origins (always allowed)
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:3001",  # Alternative dev port
]

# Production frontend URL (set via environment variable FRONTEND_URL)
# This should be your specific Vercel deployment URL
# Example: "https://nextplay.vercel.app" or "https://your-custom-domain.com"
FRONTEND_URL_ENV = "FRONTEND_URL"

# CORS regex for Vercel preview deployments (optional, more permissive)
# Set to None to disable wildcard matching (more secure - recommended)
# Only enable if you need to allow preview deployments from pull requests
# WARNING: Enabling this allows ANY Vercel deployment to access your API
VERCEL_ORIGIN_REGEX = None  # Disabled by default for security
# To enable (not recommended): r"https://.*\.vercel\.app"

# Recommendation Engine Constants
DISCOVERY_WEIGHT_BASE = 0.2  # Base weight for discovery score
DISCOVERY_WEIGHT_LEVEL_UP = 0.4  # Increased weight for experienced users (5+ milestones)
LEVEL_UP_THRESHOLD = 5  # Number of completed milestones to trigger "level up"

# Age bounds for categorization (in months)
FOUNDATIONAL_AGE_BOUND = 3.0  # Foundational: past age but within 3 months
LIKELY_AGE_TOLERANCE = 0.5  # Likely: within ±0.5 months of current age
CHALLENGE_AGE_BOUND = 3.0  # Challenge: future but within 3 months

# Urgency score normalization
MAX_URGENCY_AGE_DIFF = 12.0  # Maximum age difference for urgency score (months)

# Milestone domain mapping
DOMAIN_MAPPING = {
    'c': 'cognitive',
    'f': 'fine_motor',
    'g': 'gross_motor'
}

# API Configuration
API_TITLE = "NextPlay API"
API_DESCRIPTION = "Baby development milestone recommendations with play activities"
API_VERSION = "1.0.0"

# Data processing constants
DAYS_PER_MONTH = 30.44  # Average days per month for age conversion
MILESTONE_UNTESTED = -1  # Value for untested milestones
MILESTONE_NOT_ACHIEVED = 0  # Value for not achieved milestones
MILESTONE_ACHIEVED = 1  # Value for achieved milestones

# Age validation
MIN_AGE_MONTHS = 0
MAX_AGE_MONTHS = 48

# File encoding
DEFAULT_ENCODING = "utf-8"

