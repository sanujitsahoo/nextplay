# NextPlay Backend

Python FastAPI backend for the NextPlay baby development recommender system.

## Project Structure

```
backend/
├── models/              # Generated model files (JSON/CSV) - used in production
│   ├── processed_milestones.csv
│   ├── mastery_ages.json
│   ├── transition_matrix.json
│   ├── milestone_map.json
│   └── activities.json
│
├── training_data/       # Raw training data (not required for production)
│   ├── data/           # Raw .rda files from clinical datasets
│   └── man/            # Documentation files (.Rd)
│
├── tests/              # Test suite
│   ├── test_engine_logic.py
│   ├── test_intake_specialist.py
│   ├── test_openai_api_key.py
│   ├── verify_api_key.py
│   └── README.md
│
├── docs/               # Documentation files
│   ├── README_API.md
│   ├── README_ENV.md
│   └── README_TESTS.md
│
├── config.py           # Centralized configuration
├── engine_logic.py     # Data processing (mastery ages, transition matrix)
├── recommender.py      # Recommendation engine logic
├── intake_specialist.py # Natural language processing
├── utils.py            # Shared utility functions
├── main.py             # FastAPI application
├── setup_data.py       # Data preprocessing script (training)
└── requirements.txt    # Python dependencies
```

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment (in parent directory)
python3 -m venv ../nexplay_env
source ../nexplay_env/bin/activate  # macOS/Linux
# On Windows: ..\nexplay_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the `backend/` directory:

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

See [docs/README_ENV.md](./docs/README_ENV.md) for detailed setup instructions.

### 3. Generate Model Files (Training Phase)

**Note**: The `training_data/` folder is only needed during the training/data processing phase. For production deployment, only the `models/` folder is required.

```bash
# Process raw data and generate models
python setup_data.py      # Creates processed_milestones.csv and milestone_map.json
python engine_logic.py    # Creates mastery_ages.json and transition_matrix.json
```

This generates all required files in the `models/` directory:
- `processed_milestones.csv` - Processed milestone observations
- `milestone_map.json` - Human-readable milestone names
- `mastery_ages.json` - Typical mastery ages for each milestone
- `transition_matrix.json` - Sequential milestone patterns

### 4. Run the Server

```bash
# Development server with auto-reload
uvicorn main:app --reload --port 8000

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Training vs Production

### Training Phase (Development/Setup)

During development or when regenerating models:

1. **Required**: `training_data/` folder with raw `.rda` files and `.Rd` documentation
2. **Run**: `setup_data.py` and `engine_logic.py` to process data
3. **Output**: Generated model files in `models/` directory

### Production Phase (Deployment)

For production deployment:

1. **Not Required**: `training_data/` folder (excluded from git, not uploaded)
2. **Required**: `models/` folder with all generated JSON/CSV files
3. **Run**: Only `main.py` (FastAPI server) - reads from `models/` directory

The production system only needs:
- `models/` directory with generated files
- `main.py`, `config.py`, `recommender.py`, `engine_logic.py`, `intake_specialist.py`, `utils.py`
- `requirements.txt` for dependencies
- `.env` file (or environment variables) for API keys

## API Endpoints

### POST `/recommend`
Get personalized milestone recommendations with matching play activities.

**Request:**
```json
{
  "baby_age_months": 6.0,
  "completed_milestone_ids": ["ddicmm029", "ddigmd055"]
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "milestone_id": "ddigmd063",
      "milestone_name": "Sits in stable position without support",
      "category": "likely",
      "mastery_age": 6.5,
      "activity": {
        "title": "Independent Sitter",
        "materials": ["toys"],
        "instructions": ["...", "..."],
        "benefit": "Science Tip: ..."
      }
    }
  ]
}
```

### POST `/intake`
Process parent's natural language description using Intake Specialist.

**Request:**
```json
{
  "description": "My baby Emma is 6 months old. She can sit without support and she's starting to crawl."
}
```

**Response:**
```json
{
  "child_name": "Emma",
  "age_months": 6.0,
  "completed_milestone_ids": ["ddigmd063", "ddigmm066"],
  "needs_clarification": false,
  "follow_up_question": null
}
```

### GET `/health`
Health check endpoint.

### GET `/milestones`
List all available milestones with their activities.

See [docs/README_API.md](./docs/README_API.md) for complete API documentation.

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
# Test data processing
pytest tests/test_engine_logic.py -v

# Test intake specialist
pytest tests/test_intake_specialist.py -v

# Test API key configuration
pytest tests/test_openai_api_key.py -v

# Verify API key setup (standalone script)
python tests/verify_api_key.py
```

See [tests/README.md](./tests/README.md) for detailed testing documentation.

## Modules Overview

### `config.py`
Centralized configuration for file paths, constants, and settings.

### `engine_logic.py`
- Data loading from CSV
- Mastery age calculation
- Transition matrix generation
- File I/O for model files

### `recommender.py`
- Recommendation engine logic
- Frontier identification
- Category assignment (Foundational, Likely, Challenge)
- Age-based recommendations
- Proficiency-based filtering

### `intake_specialist.py`
- Natural language processing using OpenAI
- Milestone extraction from parent descriptions
- Age extraction and validation

### `utils.py`
- Shared utility functions
- Milestone domain extraction
- Category assignment helpers
- Diversity filtering

### `main.py`
- FastAPI application
- API endpoints
- Data loading on startup
- CORS configuration

## File Organization

### Models Directory (`models/`)
Contains all generated model files used in production:
- `processed_milestones.csv` - Processed milestone data
- `milestone_map.json` - Milestone ID to name mapping
- `mastery_ages.json` - Typical mastery ages
- `transition_matrix.json` - Sequential patterns
- `activities.json` - Play activities for milestones

**These files are required for the API to function.**

### Training Data Directory (`training_data/`)
Contains raw data files used only during training/data processing:
- `data/` - Raw `.rda` files (clinical datasets)
- `man/` - Documentation files (`.Rd` files)

**This directory is not required for production deployment and is excluded from version control.**

## Development Workflow

### Initial Setup

1. Clone repository
2. Set up virtual environment
3. Install dependencies
4. Set up `.env` file with OpenAI API key
5. Run training scripts to generate models

### Making Changes

1. Make code changes
2. Run tests: `pytest tests/ -v`
3. Regenerate models if data processing changed: `python setup_data.py && python engine_logic.py`
4. Test API: `uvicorn main:app --reload`
5. Commit changes

### Before Deployment

1. Ensure all tests pass
2. Verify `models/` directory contains all required files
3. Ensure `.env` is configured (or environment variables set)
4. Test API endpoints
5. Verify production paths in `config.py` are relative

## Additional Documentation

- [API Documentation](./docs/README_API.md) - Detailed API endpoint documentation
- [Environment Setup](./docs/README_ENV.md) - Environment variable configuration
- [Testing Guide](./tests/README.md) - Test suite documentation
- [Technical Documentation](../TECHNICAL_DOCUMENTATION.html) - Technical deep dive
- [System Architecture](../SYSTEM_ARCHITECTURE.html) - End-to-end system overview

