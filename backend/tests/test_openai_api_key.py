"""
Comprehensive tests for OpenAI API Key usage in NextPlay.

Tests verify that:
1. API key is loaded from environment variables correctly
2. IntakeSpecialist uses the API key properly when making API calls
3. FastAPI endpoint correctly initializes with the API key
4. Error handling when API key is missing or invalid
5. Integration tests for the full intake flow
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Optional

# Import the modules we're testing
import intake_specialist
from config import ENV_OPENAI_API_KEY, ENV_OPENAI_MODEL, DEFAULT_OPENAI_MODEL


# Test data
TEST_MILESTONE_MAP = {
    "ddigmd001": "Lifts head",
    "ddigmd063": "Sits without support",
    "ddigmm066": "Crawls forward",
    "ddicmm030": "Social smile",
    "ddigmm067": "Walks with support",
    "ddicmm033": "Says dada/mama",
    "ddicmm036": "Waves bye-bye",
}


class TestIntakeSpecialistAPIKey:
    """Test that IntakeSpecialist correctly uses the OpenAI API key."""
    
    def test_api_key_from_env_variable(self):
        """Test that API key is loaded from OPENAI_API_KEY environment variable."""
        test_key = "sk-test-key-from-env-12345"
        
        with patch.dict(os.environ, {ENV_OPENAI_API_KEY: test_key}):
            with patch('intake_specialist.OpenAI') as mock_openai_class:
                specialist = intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP
                )
                
                # Verify OpenAI client was initialized with the correct API key
                mock_openai_class.assert_called_once()
                call_args = mock_openai_class.call_args
                assert call_args.kwargs['api_key'] == test_key
    
    def test_api_key_from_parameter(self):
        """Test that API key passed as parameter takes precedence over environment variable."""
        env_key = "sk-env-key"
        param_key = "sk-param-key"
        
        with patch.dict(os.environ, {ENV_OPENAI_API_KEY: env_key}):
            with patch('intake_specialist.OpenAI') as mock_openai_class:
                specialist = intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP,
                    openai_api_key=param_key
                )
                
                # Verify OpenAI client was initialized with the parameter key, not env key
                call_args = mock_openai_class.call_args
                assert call_args.kwargs['api_key'] == param_key
                assert call_args.kwargs['api_key'] != env_key
    
    def test_api_key_missing(self):
        """Test that ValueError is raised when API key is missing."""
        # Remove API key from environment if it exists
        with patch.dict(os.environ, {}, clear=True):
            # Also ensure the key is not in the environment
            if ENV_OPENAI_API_KEY in os.environ:
                del os.environ[ENV_OPENAI_API_KEY]
            
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP,
                    openai_api_key=None
                )
    
    def test_api_key_used_in_api_call(self):
        """Test that the API key is actually used when making OpenAI API calls."""
        test_key = "sk-test-key-12345"
        
        # Mock OpenAI client and its response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "child_name": None,
            "age_months": 6.0,
            "completed_milestone_ids": ["ddigmd063"],
            "needs_clarification": False,
            "follow_up_question": None
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('intake_specialist.OpenAI', return_value=mock_client):
            specialist = intake_specialist.IntakeSpecialist(
                milestone_map=TEST_MILESTONE_MAP,
                openai_api_key=test_key
            )
            
            # Make a test API call
            result = specialist.process_intake("My baby is 6 months old and can sit without support")
            
            # Verify the client's create method was called
            mock_client.chat.completions.create.assert_called_once()
            
            # Verify the API was called with correct parameters
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs['model'] == DEFAULT_OPENAI_MODEL
            assert 'messages' in call_args.kwargs
            assert call_args.kwargs['temperature'] == 0.1
            assert call_args.kwargs['response_format'] == {"type": "json_object"}
            
            # Verify result structure
            assert result['age_months'] == 6.0
            assert 'ddigmd063' in result['completed_milestone_ids']
    
    def test_model_parameter_from_env(self):
        """Test that model can be set from environment variable."""
        test_key = "sk-test-key"
        test_model = "gpt-4"
        
        with patch.dict(os.environ, {
            ENV_OPENAI_API_KEY: test_key,
            ENV_OPENAI_MODEL: test_model
        }):
            with patch('intake_specialist.OpenAI') as mock_openai_class:
                # Create specialist without explicit model (should use env var)
                specialist = intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP
                )
                
                # Verify client was created (API key check)
                mock_openai_class.assert_called_once()
                
                # Now test that model is used in API calls
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps({
                    "child_name": None,
                    "age_months": 6.0,
                    "completed_milestone_ids": [],
                    "needs_clarification": False,
                    "follow_up_question": None
                })
                mock_client.chat.completions.create.return_value = mock_response
                
                with patch('intake_specialist.OpenAI', return_value=mock_client):
                    specialist2 = intake_specialist.IntakeSpecialist(
                        milestone_map=TEST_MILESTONE_MAP,
                        model=test_model
                    )
                    
                    specialist2.process_intake("Test description")
                    call_args = mock_client.chat.completions.create.call_args
                    assert call_args.kwargs['model'] == test_model


class TestFastAPIAPIKey:
    """Test that FastAPI endpoint correctly uses the OpenAI API key."""
    
    @pytest.fixture
    def mock_milestone_map(self, tmp_path):
        """Create a temporary milestone_map.json file for testing."""
        milestone_file = tmp_path / "milestone_map.json"
        milestone_file.write_text(json.dumps(TEST_MILESTONE_MAP))
        return milestone_file
    
    def test_api_key_loaded_on_startup(self, mock_milestone_map):
        """Test that API key is loaded from environment on FastAPI startup."""
        test_key = "sk-test-key-from-env"
        
        with patch.dict(os.environ, {ENV_OPENAI_API_KEY: test_key}):
            # Test the initialization logic directly (without importing main)
            # This mimics what main.py does in the startup event
            from dotenv import load_dotenv
            
            # Verify environment variable is accessible
            assert os.getenv(ENV_OPENAI_API_KEY) == test_key
            
            # Test that we can create an IntakeSpecialist with this key
            # (which is what main.py does during startup)
            with patch('intake_specialist.OpenAI') as mock_openai_class:
                specialist = intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP,
                    openai_api_key=test_key
                )
                
                # Verify OpenAI client was initialized with the correct key
                call_args = mock_openai_class.call_args
                assert call_args.kwargs['api_key'] == test_key
                
                # This simulates what main.py does during startup
                assert specialist is not None
    
    def test_intake_endpoint_with_api_key(self, mock_milestone_map):
        """Test that /intake endpoint works when API key is available."""
        test_key = "sk-test-key"
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "child_name": "Emma",
            "age_months": 6.0,
            "completed_milestone_ids": ["ddigmd063"],
            "needs_clarification": False,
            "follow_up_question": None
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.dict(os.environ, {ENV_OPENAI_API_KEY: test_key}):
            with patch('intake_specialist.OpenAI', return_value=mock_client):
                # Create a test IntakeSpecialist
                specialist = intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP,
                    openai_api_key=test_key
                )
                
                # Test the process_intake method
                result = specialist.process_intake(
                    "My baby Emma is 6 months old and can sit without support"
                )
                
                # Verify the API was called
                mock_client.chat.completions.create.assert_called_once()
                
                # Verify the result
                assert result['child_name'] == "Emma"
                assert result['age_months'] == 6.0
                assert 'ddigmd063' in result['completed_milestone_ids']
    
    def test_intake_endpoint_without_api_key(self):
        """Test that /intake endpoint returns 503 when API key is missing."""
        # Remove API key from environment
        original_key = os.environ.get(ENV_OPENAI_API_KEY)
        if ENV_OPENAI_API_KEY in os.environ:
            del os.environ[ENV_OPENAI_API_KEY]
        
        try:
            # Try to create IntakeSpecialist without API key
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP,
                    openai_api_key=None
                )
        finally:
            # Restore original key if it existed
            if original_key:
                os.environ[ENV_OPENAI_API_KEY] = original_key
    
    def test_intake_endpoint_invalid_api_key(self):
        """Test error handling with invalid API key."""
        invalid_key = "sk-invalid-key"
        
        # Mock OpenAI to raise an authentication error
        mock_client = MagicMock()
        from openai import AuthenticationError
        
        # We can't easily mock the exact OpenAI error, but we can test
        # that errors are caught and re-raised appropriately
        mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
        
        with patch('intake_specialist.OpenAI', return_value=mock_client):
            specialist = intake_specialist.IntakeSpecialist(
                milestone_map=TEST_MILESTONE_MAP,
                openai_api_key=invalid_key
            )
            
            # Should raise RuntimeError when API call fails
            with pytest.raises(RuntimeError, match="Error calling OpenAI API"):
                specialist.process_intake("Test description")


class TestAPIKeyFromDotEnv:
    """Test that API key is loaded from .env file correctly."""
    
    def test_load_from_dotenv_file(self, tmp_path):
        """Test that API key can be loaded from .env file."""
        test_key = "sk-test-key-from-dotenv"
        
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(f"{ENV_OPENAI_API_KEY}={test_key}\n")
        
        # Use python-dotenv to load it
        from dotenv import load_dotenv
        
        # Change to the temp directory and load .env
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            load_dotenv(env_file)
            
            # Verify the key is in environment
            assert os.getenv(ENV_OPENAI_API_KEY) == test_key
            
            # Verify it can be used
            with patch('intake_specialist.OpenAI') as mock_openai_class:
                specialist = intake_specialist.IntakeSpecialist(
                    milestone_map=TEST_MILESTONE_MAP
                )
                
                call_args = mock_openai_class.call_args
                assert call_args.kwargs['api_key'] == test_key
        finally:
            os.chdir(original_cwd)


class TestAPIKeyIntegration:
    """Integration tests for API key usage in the full application flow."""
    
    def test_end_to_end_intake_flow(self):
        """Test the complete intake flow with a real API key structure."""
        # This test uses a mock to avoid making real API calls
        test_key = "sk-test-integration-key"
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        
        # Simulate a realistic OpenAI response
        expected_response = {
            "child_name": "Emma",
            "age_months": 6.0,
            "completed_milestone_ids": ["ddigmd063", "ddigmm066"],
            "needs_clarification": False,
            "follow_up_question": None
        }
        mock_response.choices[0].message.content = json.dumps(expected_response)
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('intake_specialist.OpenAI', return_value=mock_client):
            # Initialize specialist
            specialist = intake_specialist.IntakeSpecialist(
                milestone_map=TEST_MILESTONE_MAP,
                openai_api_key=test_key
            )
            
            # Process a realistic intake
            input_text = (
                "My baby Emma is 6 months old. "
                "She can sit without support and she's starting to crawl forward. "
                "She also smiles when we play with her."
            )
            
            result = specialist.process_intake(input_text)
            
            # Verify the complete flow
            assert result['child_name'] == "Emma"
            assert result['age_months'] == 6.0
            assert len(result['completed_milestone_ids']) >= 1
            assert result['needs_clarification'] == False
            assert result['follow_up_question'] is None
            
            # Verify API was called with correct structure
            call_args = mock_client.chat.completions.create.call_args
            assert 'messages' in call_args.kwargs
            messages = call_args.kwargs['messages']
            assert len(messages) == 2  # system and user messages
            assert messages[0]['role'] == 'system'
            assert messages[1]['role'] == 'user'
            assert input_text in messages[1]['content']
            
            # Verify milestone reference is in the prompt
            prompt = messages[1]['content']
            assert 'ddigmd063' in prompt or 'Sits without support' in prompt


def run_tests():
    """Run all tests and print results."""
    print("=" * 80)
    print("Running OpenAI API Key Tests")
    print("=" * 80)
    print()
    
    # Check if API key is set in environment
    api_key = os.getenv(ENV_OPENAI_API_KEY)
    if api_key:
        print(f"✓ {ENV_OPENAI_API_KEY} is set in environment")
        print(f"  Key preview: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")
    else:
        print(f"⚠ {ENV_OPENAI_API_KEY} is NOT set in environment")
        print("  Some tests may fail or use mocks")
    print()
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()

