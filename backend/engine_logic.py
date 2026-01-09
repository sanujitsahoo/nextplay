"""
Engine logic for NextPlay baby development recommender.

This module provides data processing and loading functionality:
- Calculates mastery ages (median age at which milestones are achieved)
- Builds transition matrices (probabilistic sequences of milestone mastery)
- Loads and saves milestone data (mastery ages, transition matrix, milestone map)

Note: Recommendation logic has been moved to recommender.py
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional, Set, Tuple, Union
import numpy as np

from config import (
    PROCESSED_CSV,
    MILESTONE_MAP_JSON,
    MASTERY_AGES_JSON,
    TRANSITION_MATRIX_JSON,
    ACTIVITIES_JSON,
    DEFAULT_ENCODING,
    DAYS_PER_MONTH,
    MILESTONE_UNTESTED,
    MODELS_DIR
)
# Utility functions moved to utils.py
# Recommendation functions moved to recommender.py

def load_data(csv_file: Optional[str] = None) -> pd.DataFrame:
    """
    Load the processed milestones CSV file.
    
    Args:
        csv_file: Optional path to CSV file (defaults to config.PROCESSED_CSV)
    
    Returns:
        DataFrame containing milestone data with columns:
        - subjid: Child identifier
        - age_months: Age in months
        - sex: Child's sex
        - ddi*: Milestone columns (values: -1=untested, 0=not achieved, 1=achieved)
    
    Raises:
        FileNotFoundError: If CSV file doesn't exist
    """
    file_path = csv_file or str(PROCESSED_CSV)
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} rows for {df['subjid'].nunique()} children")
    return df

def get_milestone_columns(df: pd.DataFrame) -> List[str]:
    """
    Extract milestone column names from DataFrame.
    
    Milestone columns follow the GSED naming convention: ddi[domain][type][number]
    
    Args:
        df: DataFrame containing milestone data
    
    Returns:
        List of column names starting with 'ddi'
    
    Example:
        >>> df = pd.DataFrame({'subjid': [1], 'ddigmd055': [1], 'ddicmm030': [0]})
        >>> get_milestone_columns(df)
        ['ddigmd055', 'ddicmm030']
    """
    milestone_cols = [col for col in df.columns if col.startswith('ddi')]
    return milestone_cols

def calculate_mastery_age(df: pd.DataFrame, milestone_col: str) -> Optional[float]:
    """
    Calculate the mastery age for a milestone.
    
    Mastery age is the median age (in months) at which children transition
    from not achieving (0) to achieving (1) a milestone. This represents
    the typical age at which the milestone is mastered.
    
    Args:
        df: DataFrame containing milestone data with 'subjid' and 'age_months' columns
        milestone_col: Column name of the milestone to analyze
    
    Returns:
        Median mastery age in months, or None if no transitions found
    
    Algorithm:
        1. For each child, track chronological progression of milestone values
        2. Identify first 0→1 transition (ignoring -1/untested values)
        3. Calculate median of all transition ages across children
    
    Example:
        >>> df = pd.DataFrame({
        ...     'subjid': [1, 1, 2, 2],
        ...     'age_months': [3.0, 4.0, 3.5, 4.5],
        ...     'ddigmd055': [0, 1, 0, 1]
        ... })
        >>> calculate_mastery_age(df, 'ddigmd055')
        4.25
    """
    transitions = []
    
    for subjid in df['subjid'].unique():
        child_data = df[df['subjid'] == subjid].sort_values('age_months')
        
        # Track values chronologically, ignoring -1
        values_with_age = [
            (row['age_months'], row[milestone_col])
            for _, row in child_data.iterrows()
            if row[milestone_col] != -1
        ]
        
        if len(values_with_age) < 2:
            continue
        
        # Look for transition from 0 to 1
        for i in range(1, len(values_with_age)):
            prev_age, prev_value = values_with_age[i-1]
            current_age, current_value = values_with_age[i]
            
            # Transition from 0 to 1
            if prev_value == 0 and current_value == 1:
                transitions.append(current_age)
                # Only count the first transition for this child
                break
    
    if len(transitions) == 0:
        return None
    
    mastery_age = np.median(transitions)
    return mastery_age

def calculate_all_mastery_ages(df, milestone_cols):
    """Calculate mastery age for all milestones."""
    print("\nCalculating mastery ages...")
    mastery_ages = {}
    
    for i, milestone in enumerate(milestone_cols, 1):
        mastery_age = calculate_mastery_age(df, milestone)
        mastery_ages[milestone] = mastery_age
        if mastery_age is not None:
            print(f"  [{i}/{len(milestone_cols)}] {milestone}: {mastery_age:.2f} months")
        else:
            print(f"  [{i}/{len(milestone_cols)}] {milestone}: No transitions found")
    
    return mastery_ages

def create_transition_matrix(df, milestone_cols):
    """
    Create a transition matrix showing what milestone children master next
    after mastering a given milestone.
    
    For each child who mastered milestone X at age A, find the next milestone Y
    they master (at the earliest age > A where a milestone transitions to 1).
    
    Returns a dictionary: {milestone_X: [(milestone_Y, probability), ...]}
    """
    print("\nCreating transition matrix...")
    
    # Track transitions: milestone_X -> milestone_Y
    transitions = defaultdict(lambda: defaultdict(int))
    
    # Process each child separately
    for subjid in df['subjid'].unique():
        child_data = df[df['subjid'] == subjid].sort_values('age_months')
        
        # Track transitions for this child
        # For each row, identify milestones that transition from 0 to 1 or from -1/0 to 1
        milestone_first_mastered = {}  # Track first time a milestone becomes 1
        
        # First, identify when each milestone transitions to 1 (mastered)
        for milestone in milestone_cols:
            # Get all non-untested values for this milestone, sorted by age
            milestone_data = [
                (row['age_months'], row[milestone])
                for _, row in child_data.iterrows()
                if row[milestone] != -1
            ]
            
            if len(milestone_data) < 2:
                continue
            
            # Look for transition from 0 to 1
            for i in range(1, len(milestone_data)):
                prev_age, prev_value = milestone_data[i-1]
                current_age, current_value = milestone_data[i]
                
                if prev_value == 0 and current_value == 1:
                    milestone_first_mastered[milestone] = current_age
                    break
        
        # Now find the next milestone mastered after each milestone
        # Sort milestones by when they were mastered
        mastered_list = sorted(milestone_first_mastered.items(), key=lambda x: x[1])
        
        # For each milestone X, find the next milestone Y mastered after it
        for i, (milestone_x, age_x) in enumerate(mastered_list):
            # Find the next milestone mastered after milestone_x
            next_milestone = None
            next_age = float('inf')
            
            for milestone_y, age_y in mastered_list:
                if milestone_y != milestone_x and age_y > age_x and age_y < next_age:
                    next_milestone = milestone_y
                    next_age = age_y
            
            if next_milestone:
                transitions[milestone_x][next_milestone] += 1
    
    # Convert to probability dictionary
    transition_probs = {}
    
    for milestone_x in milestone_cols:
        if milestone_x not in transitions or len(transitions[milestone_x]) == 0:
            transition_probs[milestone_x] = []
            continue
        
        # Get all transitions from milestone_x
        next_milestones = transitions[milestone_x]
        total_transitions = sum(next_milestones.values())
        
        # Calculate probabilities and sort by probability (descending)
        prob_list = [
            (milestone_y, count / total_transitions)
            for milestone_y, count in next_milestones.items()
        ]
        prob_list.sort(key=lambda x: x[1], reverse=True)
        
        transition_probs[milestone_x] = prob_list
        
        # Print progress for milestones with transitions
        if len(prob_list) > 0:
            print(f"  {milestone_x}: {total_transitions} transitions, top next: {prob_list[0][0]} ({prob_list[0][1]:.2%})")
    
    return transition_probs

def save_results(mastery_ages, transition_matrix, milestone_map=None):
    """Save the calculated results to JSON files in the models directory."""
    print("\nSaving results...")
    
    # Ensure models directory exists
    MODELS_DIR.mkdir(exist_ok=True)
    
    # Save mastery ages
    mastery_output = {
        milestone: float(age) if age is not None else None
        for milestone, age in mastery_ages.items()
    }
    
    with open(MASTERY_AGES_JSON, 'w', encoding='utf-8') as f:
        json.dump(mastery_output, f, indent=2)
    print(f"  Saved {MASTERY_AGES_JSON.name}")
    
    # Save transition matrix with probabilities
    transition_output = {
        milestone: [
            {"milestone": next_milestone, "probability": round(prob, 4)}
            for next_milestone, prob in transitions
        ]
        for milestone, transitions in transition_matrix.items()
    }
    
    with open(TRANSITION_MATRIX_JSON, 'w', encoding='utf-8') as f:
        json.dump(transition_output, f, indent=2)
    print(f"  Saved {TRANSITION_MATRIX_JSON.name}")
    
    # Also create the simplified "Next Likely Milestones" dictionary
    # (just milestone IDs, sorted by probability)
    next_likely_milestones = {
        milestone: [next_milestone for next_milestone, _ in transitions]
        for milestone, transitions in transition_matrix.items()
    }
    
    next_likely_path = MODELS_DIR / "next_likely_milestones.json"
    with open(next_likely_path, 'w', encoding='utf-8') as f:
        json.dump(next_likely_milestones, f, indent=2)
    print(f"  Saved {next_likely_path.name}")
    
    return next_likely_milestones

def load_transition_matrix(file_path: Optional[str] = None) -> Dict[str, List[Tuple[str, float]]]:
    """
    Load the transition matrix from JSON file.
    
    The transition matrix maps each milestone to a list of next likely milestones
    with their transition probabilities.
    
    Args:
        file_path: Optional path to transition matrix JSON file 
                   (defaults to config.TRANSITION_MATRIX_JSON)
    
    Returns:
        Dictionary mapping milestone IDs to lists of (next_milestone, probability) tuples
    
    Raises:
        FileNotFoundError: If transition matrix file doesn't exist
    
    Example:
        >>> matrix = load_transition_matrix()
        >>> matrix['ddigmd055']
        [('ddigmd061', 0.45), ('ddigmd062', 0.32), ...]
    """
    path = file_path or str(TRANSITION_MATRIX_JSON)
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Transition matrix file not found: {path}. "
            "Run main() first to generate it."
        )
    
    with open(path, 'r', encoding=DEFAULT_ENCODING) as f:
        data = json.load(f)
    
    # Convert back to list of tuples format: [(milestone_Y, probability), ...]
    transition_matrix = {}
    for milestone_x, transitions in data.items():
        transition_matrix[milestone_x] = [
            (item["milestone"], item["probability"])
            for item in transitions
        ]
    return transition_matrix

def load_mastery_ages(file_path: Optional[str] = None) -> Dict[str, Optional[float]]:
    """
    Load mastery ages from JSON file.
    
    Mastery ages represent the median age (in months) at which children
    typically achieve each milestone.
    
    Args:
        file_path: Optional path to mastery ages JSON file 
                   (defaults to config.MASTERY_AGES_JSON)
    
    Returns:
        Dictionary mapping milestone IDs to mastery ages (None if not available)
    
    Raises:
        FileNotFoundError: If mastery ages file doesn't exist
    
    Example:
        >>> ages = load_mastery_ages()
        >>> ages['ddigmd055']
        3.08
    """
    path = file_path or str(MASTERY_AGES_JSON)
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Mastery ages file not found: {path}. "
            "Run main() first to generate it."
        )
    
    with open(path, 'r', encoding=DEFAULT_ENCODING) as f:
        mastery_ages = json.load(f)
    # Convert None strings back to None
    return {k: (v if v is not None else None) for k, v in mastery_ages.items()}

def load_milestone_map(file_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load milestone map from JSON file.
    
    The milestone map provides human-readable names for milestone codes.
    
    Args:
        file_path: Optional path to milestone map JSON file 
                   (defaults to config.MILESTONE_MAP_JSON)
    
    Returns:
        Dictionary mapping milestone IDs to human-readable names
    
    Example:
        >>> map_data = load_milestone_map()
        >>> map_data['ddigmd055']
        'No head lag if pulled to sitting'
    """
    path = file_path or str(MILESTONE_MAP_JSON)
    if not Path(path).exists():
        print(f"Warning: Milestone map file not found: {path}")
        return {}
    with open(path, 'r', encoding=DEFAULT_ENCODING) as f:
        return json.load(f)

# get_milestone_domain moved to utils.py
# Recommendation functions (get_recommendations, _calculate_milestone_frequencies, _get_age_based_recommendations) moved to recommender.py

def print_summary(mastery_ages, transition_matrix, milestone_map=None):
    """Print a summary of the results."""
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    # Mastery ages summary
    valid_mastery_ages = {k: v for k, v in mastery_ages.items() if v is not None}
    print(f"\nMastery Ages:")
    print(f"  Total milestones: {len(mastery_ages)}")
    print(f"  Milestones with valid mastery age: {len(valid_mastery_ages)}")
    
    if valid_mastery_ages:
        sorted_ages = sorted(valid_mastery_ages.items(), key=lambda x: x[1])
        print(f"\n  Earliest mastery: {sorted_ages[0][0]} at {sorted_ages[0][1]:.2f} months")
        if milestone_map:
            print(f"    ({milestone_map.get(sorted_ages[0][0], 'Unknown')})")
        
        print(f"  Latest mastery: {sorted_ages[-1][0]} at {sorted_ages[-1][1]:.2f} months")
        if milestone_map:
            print(f"    ({milestone_map.get(sorted_ages[-1][0], 'Unknown')})")
    
    # Transition matrix summary
    milestones_with_transitions = sum(1 for v in transition_matrix.values() if len(v) > 0)
    print(f"\nTransition Matrix:")
    print(f"  Milestones with next-step transitions: {milestones_with_transitions}/{len(transition_matrix)}")
    
    # Show some example transitions
    print(f"\n  Example transitions (top 3 most common next steps):")
    count = 0
    for milestone, transitions in transition_matrix.items():
        if len(transitions) > 0 and count < 3:
            print(f"    {milestone}:")
            if milestone_map:
                print(f"      '{milestone_map.get(milestone, 'Unknown')}'")
            for next_milestone, prob in transitions[:3]:
                next_label = milestone_map.get(next_milestone, 'Unknown') if milestone_map else 'Unknown'
                print(f"      -> {next_milestone} ({prob:.2%}): {next_label}")
            count += 1

def main():
    """Main function."""
    print("=" * 60)
    print("NextPlay Engine Logic")
    print("=" * 60)
    
    # Load data
    df = load_data()
    
    # Get milestone columns
    milestone_cols = get_milestone_columns(df)
    print(f"Found {len(milestone_cols)} milestone columns")
    
    # Load milestone map if available
    milestone_map = None
    if MILESTONE_MAP_JSON.exists():
        with open(MILESTONE_MAP_JSON, 'r', encoding=DEFAULT_ENCODING) as f:
            milestone_map = json.load(f)
        print(f"Loaded milestone map with {len(milestone_map)} entries")
    
    # Calculate mastery ages
    mastery_ages = calculate_all_mastery_ages(df, milestone_cols)
    
    # Create transition matrix
    transition_matrix = create_transition_matrix(df, milestone_cols)
    
    # Save results
    next_likely_milestones = save_results(mastery_ages, transition_matrix, milestone_map)
    
    # Print summary
    print_summary(mastery_ages, transition_matrix, milestone_map)
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)

def example_recommendations():
    """Example usage of get_recommendations function from recommender module."""
    from recommender import get_recommendations
    
    print("\n" + "=" * 60)
    print("Example Recommendations")
    print("=" * 60)
    
    # Example 1: New user (empty completed milestones)
    print("\n--- Example 1: New User (no completed milestones) ---")
    baby_age_new = 3.0
    print(f"Baby age: {baby_age_new} months")
    print("Completed milestones: [] (new user)")
    
    recommendations_new = get_recommendations([], baby_age_new)
    
    if recommendations_new:
        print("\nTop 3 Recommendations (balanced mix):")
        for i, rec in enumerate(recommendations_new, 1):
            print(f"\n  {i}. {rec['milestone_id']} [{rec.get('category', 'unknown').upper()}]")
            print(f"     Name: {rec['milestone_name']}")
            print(f"     Probability: {rec['probability']:.2%}")
            print(f"     Discovery Score: {rec.get('discovery_score', 0):.2%}")
            print(f"     Foundation Score: {rec['foundation_score']:.2f}")
            if rec['mastery_age']:
                age_diff = baby_age_new - rec['mastery_age']
                print(f"     Typical Mastery Age: {rec['mastery_age']:.2f} months")
                if age_diff > 0:
                    print(f"     (Baby is {age_diff:.1f} months past typical age - FOUNDATIONAL)")
                elif age_diff < -0.5:
                    print(f"     (Advanced milestone - CHALLENGE)")
                else:
                    print(f"     (Age-appropriate - LIKELY)")
    
    # Example 2: Existing user with completed milestones
    print("\n--- Example 2: Existing User (with completed milestones) ---")
    user_completed = ["ddicmm029", "ddicmm030", "ddigmd055", "ddifmd001"]
    baby_age = 6.0
    
    print(f"\nBaby age: {baby_age} months")
    print(f"Completed milestones: {user_completed}")
    
    recommendations = get_recommendations(user_completed, baby_age)
    
    if recommendations:
        print("\nTop 3 Recommendations (balanced mix):")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n  {i}. {rec['milestone_id']} [{rec.get('category', 'unknown').upper()}]")
            print(f"     Name: {rec['milestone_name']}")
            print(f"     Transition Probability: {rec['probability']:.2%}")
            print(f"     Discovery Score: {rec.get('discovery_score', 0):.2%}")
            print(f"     Foundation Score: {rec['foundation_score']:.2f}")
            if rec['mastery_age']:
                age_diff = baby_age - rec['mastery_age']
                print(f"     Typical Mastery Age: {rec['mastery_age']:.2f} months")
                category = rec.get('category', 'unknown')
                if category == 'foundational':
                    print(f"     (Baby is {age_diff:.1f} months past typical age - FOUNDATIONAL)")
                elif category == 'challenge':
                    print(f"     (Advanced milestone - CHALLENGE)")
                else:
                    print(f"     (Natural next step - LIKELY)")
    else:
        print("\nNo recommendations found. Make sure transition_matrix.json and mastery_ages.json exist.")
        print("Run the main() function first to generate these files.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "recommendations":
        # Run example recommendations
        example_recommendations()
    else:
        # Run main processing
        main()

