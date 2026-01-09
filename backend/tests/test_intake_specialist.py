"""
Test cases for the NextPlay Intake Specialist
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import intake_specialist
from config import MILESTONE_MAP_JSON


def test_intake_specialist():
    """Test the intake specialist with various parent descriptions."""
    
    # Load milestone map from models folder
    milestone_map_path = MILESTONE_MAP_JSON
    if not milestone_map_path.exists():
        print(f"❌ milestone_map.json not found at {milestone_map_path}. Please run setup_data.py first.")
        return
    
    with open(milestone_map_path, 'r', encoding='utf-8') as f:
        milestone_map = json.load(f)
    
    # Initialize specialist (API key should be in environment or .env file)
    try:
        specialist = intake_specialist.IntakeSpecialist(milestone_map)
    except ValueError as e:
        print(f"❌ Cannot initialize IntakeSpecialist: {e}")
        print("Please ensure OPENAI_API_KEY is set in your .env file or environment.")
        return
    
    test_cases = [
        {
            "description": "My baby Emma is 6 months old. She can sit without support and she's starting to crawl. She also smiles when we play with her.",
            "expected_age": 6.0,
            "expected_milestones": ["ddigmd063", "ddigmm066", "ddicmm030"],  # Approximate
            "expected_clarification": False
        },
        {
            "description": "My son is almost 1 year old. He can walk while holding onto furniture.",
            "expected_age": None,  # "almost" is ambiguous
            "expected_milestones": ["ddigmm067"],
            "expected_clarification": True
        },
        {
            "description": "My baby is 18 months. She says dada and baba, and she waves bye-bye.",
            "expected_age": 18.0,
            "expected_milestones": ["ddicmm033", "ddicmm036"],
            "expected_clarification": False
        },
        {
            "description": "He's 8 months and can pull himself up to standing.",
            "expected_age": 8.0,
            "expected_milestones": ["ddigmm065"],
            "expected_clarification": False
        },
        {
            "description": "My child is 3 months old. Not much yet, just starting to hold head up.",
            "expected_age": 3.0,
            "expected_milestones": [],  # "hold head up" might not match exactly
            "expected_clarification": False
        },
        {
            "description": "She's 12 weeks and can grasp objects within reach.",
            "expected_age": 12.0 / 4.33,  # Approximately 2.8 months
            "expected_milestones": ["ddigmd006"],
            "expected_clarification": False
        },
    ]
    
    print("=" * 80)
    print("Testing NextPlay Intake Specialist")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {test_case['description']}")
        
        result = specialist.process_intake(test_case['description'])
        
        print(f"\nResult:")
        print(json.dumps(result, indent=2))
        
        # Check age
        if test_case['expected_age'] is None:
            assert result['age_months'] is None, f"Expected None, got {result['age_months']}"
        else:
            if result['age_months'] is not None:
                assert abs(result['age_months'] - test_case['expected_age']) < 0.5, \
                    f"Age mismatch: expected ~{test_case['expected_age']}, got {result['age_months']}"
        
        # Check milestones (at least some matches)
        if test_case['expected_milestones']:
            found_any = any(milestone in result['completed_milestone_ids'] 
                          for milestone in test_case['expected_milestones'])
            if found_any:
                print(f"✓ Found expected milestone(s)")
            else:
                print(f"⚠ Warning: Expected milestones {test_case['expected_milestones']} not found")
                print(f"  Found instead: {result['completed_milestone_ids']}")
        
        # Check clarification
        assert result['needs_clarification'] == test_case['expected_clarification'], \
            f"Clarification mismatch: expected {test_case['expected_clarification']}, got {result['needs_clarification']}"
        
        if result['needs_clarification']:
            assert result['follow_up_question'] is not None, "Follow-up question should be provided"
            print(f"✓ Clarification needed: {result['follow_up_question']}")
        
        print("✓ Test passed")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    test_intake_specialist()

