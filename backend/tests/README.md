# NextPlay Backend Tests

This directory contains the test suite for the NextPlay backend.

## Test Files

- **`test_engine_logic.py`**: Unit tests for data processing, mastery age calculation, and transition matrix generation
- **`test_intake_specialist.py`**: Tests for the Intake Specialist natural language processing
- **`test_openai_api_key.py`**: Tests to verify OpenAI API key configuration and usage
- **`verify_api_key.py`**: Standalone script to verify API key setup (can be run directly)

## Running Tests

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Run Specific Test File

```bash
# Test engine logic
pytest tests/test_engine_logic.py -v

# Test intake specialist
pytest tests/test_intake_specialist.py -v

# Test API key configuration
pytest tests/test_openai_api_key.py -v
```

### Verify API Key Setup

```bash
# Run the verification script directly
python tests/verify_api_key.py
```

## Test Coverage

The test suite covers:

1. **Data Loading**: CSV file loading, milestone column extraction
2. **Mastery Age Calculation**: Median age calculation for milestone transitions
3. **Transition Matrix**: Sequential milestone pattern detection
4. **Recommendation Engine**: 
   - New user recommendations (age-based)
   - Existing user recommendations (transition-based)
   - Category assignment (Foundational, Likely, Challenge)
   - Domain diversity filtering
   - Proficiency-based age restrictions
5. **Intake Specialist**: Natural language parsing, milestone extraction, age extraction
6. **API Integration**: API key loading, FastAPI startup

## Prerequisites

Before running tests, ensure:

1. **Models are generated**: Run `python setup_data.py` and `python engine_logic.py` to generate required JSON files
2. **Environment variables**: For intake specialist tests, `OPENAI_API_KEY` must be set in `.env` file
3. **Dependencies**: All packages from `requirements.txt` are installed

## Adding New Tests

When adding new functionality:

1. Create corresponding test functions in the appropriate test file
2. Use descriptive test names (e.g., `test_get_recommendations_for_new_user`)
3. Include both positive and negative test cases
4. Mock external dependencies (API calls, file I/O) when appropriate
5. Update this README if adding new test files

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- After major refactoring
- When adding new features

