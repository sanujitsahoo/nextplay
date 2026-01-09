"""
Recommendation engine for NextPlay baby development recommender.

This module provides personalized milestone recommendations based on:
- User's completed milestones
- Baby's current age
- Transition probabilities between milestones
- Milestone mastery ages
- Domain diversity (Cognitive, Fine Motor, Gross Motor)

The recommendation engine ensures a balanced mix of:
- Foundational milestones (past typical age, need to catch up)
- Likely milestones (high-probability next steps)
- Challenge milestones (advanced future development)

All recommendations respect proficiency-based filtering to avoid recommending
milestones that are too young for babies who have demonstrated age-appropriate progress.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional, Set

from config import (
    PROCESSED_CSV,
    MILESTONE_MAP_JSON,
    MASTERY_AGES_JSON,
    TRANSITION_MATRIX_JSON,
    ACTIVITIES_JSON,
    DISCOVERY_WEIGHT_BASE,
    DISCOVERY_WEIGHT_LEVEL_UP,
    LEVEL_UP_THRESHOLD,
    DEFAULT_ENCODING,
)
import pandas as pd

from engine_logic import (
    load_mastery_ages,
    load_milestone_map,
    load_transition_matrix,
    get_milestone_columns,
)
from utils import (
    get_milestone_domain,
    categorize_milestone_by_age,
    calculate_urgency_score,
    add_milestone_with_diversity_check,
    calculate_weighted_score,
)


def get_recommendations(user_completed_ids, baby_age_months, 
                       transition_matrix_file=None,
                       mastery_ages_file=None,
                       milestone_map_file=None,
                       csv_file=None,
                       activities_file=None,
                       transition_matrix_data=None,
                       mastery_ages_data=None,
                       milestone_map_data=None,
                       activities_data=None):
    """
    Get personalized milestone recommendations for a baby.
    
    Returns a balanced mix of 3 recommendations:
    - 1 'Foundational': Milestones past the baby's age (need to catch up)
    - 1 'Likely': High-probability next steps (natural progression)
    - 1 'Challenge': Advanced milestones (future development)
    
    Args:
        user_completed_ids: List of milestone IDs the user has completed (empty list for new users)
        baby_age_months: Current age of the baby in months (float)
        transition_matrix_file: Path to transition matrix JSON file (defaults to config.TRANSITION_MATRIX_JSON)
        mastery_ages_file: Path to mastery ages JSON file (defaults to config.MASTERY_AGES_JSON)
        milestone_map_file: Path to milestone map JSON file (defaults to config.MILESTONE_MAP_JSON)
        csv_file: Path to processed milestones CSV file (defaults to config.PROCESSED_CSV)
        activities_file: Path to activities JSON file (defaults to config.ACTIVITIES_JSON)
        transition_matrix_data: Optional pre-loaded transition matrix dictionary (avoids file I/O)
        mastery_ages_data: Optional pre-loaded mastery ages dictionary (avoids file I/O)
        milestone_map_data: Optional pre-loaded milestone map dictionary (avoids file I/O)
        activities_data: Optional pre-loaded activities dictionary (avoids file I/O)
    
    Returns:
        List of up to 3 dictionaries, each containing:
        - 'milestone_id': Milestone ID string
        - 'milestone_name': Human-readable milestone name
        - 'probability': Transition probability (or frequency-based score for new users)
        - 'discovery_score': Discovery score (1 - probability), higher for rare/advanced milestones
        - 'foundation_score': Foundation score (0-1, higher = more foundational/urgent)
        - 'category': Recommendation category ('foundational', 'likely', or 'challenge')
        - 'mastery_age': Typical mastery age in months
    """
    if baby_age_months < 0:
        raise ValueError("baby_age_months must be non-negative")
    
    # Use config defaults if file paths are None
    if transition_matrix_file is None:
        transition_matrix_file = str(TRANSITION_MATRIX_JSON)
    if mastery_ages_file is None:
        mastery_ages_file = str(MASTERY_AGES_JSON)
    if milestone_map_file is None:
        milestone_map_file = str(MILESTONE_MAP_JSON)
    if csv_file is None:
        csv_file = str(PROCESSED_CSV)
    if activities_file is None:
        activities_file = str(ACTIVITIES_JSON)
    
    # Load activities to filter recommendations
    if activities_data is not None:
        # activities_data can be either a set or a dict
        if isinstance(activities_data, set):
            available_milestone_ids = activities_data
        else:
            available_milestone_ids = set(activities_data.keys())
    else:
        # Load activities file to get list of milestones with activities
        activities_path = Path(activities_file)
        if activities_path.exists():
            with open(activities_path, 'r', encoding='utf-8') as f:
                activities_list = json.load(f)
            available_milestone_ids = {activity.get("target_milestone_id") for activity in activities_list if activity.get("target_milestone_id")}
        else:
            # If activities file doesn't exist, don't filter (for backward compatibility)
            available_milestone_ids = None
    
    # Use provided data if available, otherwise load from files
    if mastery_ages_data is not None:
        mastery_ages = mastery_ages_data
    else:
        mastery_ages = load_mastery_ages(mastery_ages_file)
    
    if milestone_map_data is not None:
        milestone_map = milestone_map_data
    else:
        milestone_map = load_milestone_map(milestone_map_file)
    
    # Handle new users (empty completed milestones)
    if not user_completed_ids:
        # Find age-appropriate milestones and sort by frequency
        return _get_age_based_recommendations(
            baby_age_months, mastery_ages, milestone_map, csv_file, available_milestone_ids
        )
    
    # Use provided transition matrix if available, otherwise load from file
    if transition_matrix_data is not None:
        transition_matrix = transition_matrix_data
    else:
        transition_matrix = load_transition_matrix(transition_matrix_file)
    
    # Filter for frontier milestones
    # Aggregate transition probabilities from all completed milestones
    frontier_scores = defaultdict(float)
    
    for completed_id in user_completed_ids:
        if completed_id not in transition_matrix:
            continue
        
        # For each completed milestone, get its transition probabilities
        for next_milestone, probability in transition_matrix[completed_id]:
            # Only consider milestones not yet completed
            if next_milestone not in user_completed_ids:
                # Aggregate probabilities (take maximum for simplicity)
                # This gives higher weight to milestones that are common next steps
                # from multiple completed milestones
                frontier_scores[next_milestone] = max(
                    frontier_scores[next_milestone], 
                    probability
                )
    
    # Strict exclusion check: Filter out all completed milestones
    completed_set = set(user_completed_ids)
    frontier_scores = {
        milestone_id: prob 
        for milestone_id, prob in frontier_scores.items() 
        if milestone_id not in completed_set  # Strict exclusion
    }
    
    # Filter frontier scores to only include milestones with activities
    if available_milestone_ids is not None:
        frontier_scores = {
            milestone_id: prob 
            for milestone_id, prob in frontier_scores.items() 
            if milestone_id in available_milestone_ids and milestone_id not in completed_set  # Double-check exclusion
        }
    
    # If no frontier milestones found, skip to fallback logic at the end
    # We'll handle empty results by falling back to age-based recommendations
    # Dynamic weighting: Increase discovery_score weight for users with 5+ completed milestones
    num_completed = len(user_completed_ids)
    discovery_weight = DISCOVERY_WEIGHT_LEVEL_UP if num_completed >= LEVEL_UP_THRESHOLD else DISCOVERY_WEIGHT_BASE
    
    # Calculate baby's proficiency level: How many milestones have they completed that are at/above their age?
    # This helps us avoid recommending milestones that are too young
    completed_set = set(user_completed_ids)
    age_appropriate_completed = 0
    for completed_id in completed_set:
        mastery_age = mastery_ages.get(completed_id)
        if mastery_age is not None:
            # Count milestones that are at or near baby's current age (within 1 month below or at/above)
            # This indicates the baby is progressing well and doesn't need younger milestones
            if mastery_age >= baby_age_months - 1.0:  # Milestone at or slightly below/above baby's age
                age_appropriate_completed += 1
    
    # Determine if we should restrict foundational (past age) recommendations
    # If baby has completed 2+ age-appropriate milestones, they've demonstrated proficiency
    # In this case, avoid recommending milestones that are significantly below their age
    restrict_foundational = age_appropriate_completed >= 2
    max_foundational_age_diff = 1.0 if restrict_foundational else 3.0  # Only allow 1 month past if proficient
    # Additionally, if proficient, never recommend milestones more than 2 months below baby's age
    min_allowed_mastery_age = baby_age_months - 2.0 if restrict_foundational else None
    
    if restrict_foundational:
        print(f"✓ Baby has completed {age_appropriate_completed} age-appropriate milestones. Prioritizing milestones at/above current age.")
    
    # Calculate scores and categorize milestones
    # Categories: Foundational (past age), Likely (high probability), Challenge (future age)
    foundational_milestones = []
    likely_milestones = []
    challenge_milestones = []
    
    if len(frontier_scores) > 0:
        for milestone_id, transition_prob in frontier_scores.items():
            mastery_age = mastery_ages.get(milestone_id)
            
            # Calculate discovery score (helps surface rare/advanced milestones)
            discovery_score = 1.0 - transition_prob
            
            # Calculate urgency score and categorize
            if mastery_age is not None:
                age_difference = baby_age_months - mastery_age
                urgency_score = calculate_urgency_score(age_difference)
                
                milestone_info = {
                    'milestone_id': milestone_id,
                    'transition_probability': transition_prob,
                    'discovery_score': discovery_score,
                    'foundation_score': urgency_score,  # Renamed from urgency_score
                    'mastery_age': mastery_age,
                    'age_difference': age_difference,
                    'domain': get_milestone_domain(milestone_id)
                }
                
                # Categorize milestone using utility function
                category = categorize_milestone_by_age(age_difference)
                
                # If baby has shown proficiency, restrict foundational milestones to only those very close to current age
                if restrict_foundational:
                    # Never recommend milestones that are significantly below baby's age
                    if min_allowed_mastery_age is not None and mastery_age < min_allowed_mastery_age:
                        continue  # Skip milestones that are too young
                    # If it's foundational, only include if very close (within 1 month)
                    if category == 'foundational':
                        if age_difference <= max_foundational_age_diff:
                            milestone_info['category'] = category
                            foundational_milestones.append(milestone_info)
                        # Otherwise, treat as likely if close enough, or skip
                        elif abs(age_difference) <= 1.5:
                            milestone_info['category'] = 'likely'
                            likely_milestones.append(milestone_info)
                        # Skip milestones that are too far in the past
                        continue
                
                # Normal categorization for non-proficient babies or milestones that pass proficiency check
                if category:
                    milestone_info['category'] = category
                    if category == 'foundational':
                        foundational_milestones.append(milestone_info)
                    elif category == 'likely':
                        likely_milestones.append(milestone_info)
                    elif category == 'challenge':
                        challenge_milestones.append(milestone_info)
                # Ignore milestones outside reasonable bounds
            else:
                # No mastery age data - treat as likely if high probability, else challenge
                milestone_info = {
                    'milestone_id': milestone_id,
                    'transition_probability': transition_prob,
                    'discovery_score': discovery_score,
                    'foundation_score': 0.0,  # Renamed from urgency_score
                    'mastery_age': None,
                    'age_difference': 0,
                    'domain': get_milestone_domain(milestone_id)
                }
                if transition_prob >= 0.5:
                    milestone_info['category'] = 'likely'
                    likely_milestones.append(milestone_info)
                else:
                    milestone_info['category'] = 'challenge'
                    challenge_milestones.append(milestone_info)
    
    # Sort each category appropriately
    # Foundational: Sort by mastery_age (most recent first), then by probability
    foundational_milestones.sort(
        key=lambda x: (x.get('mastery_age', 0), x['transition_probability']), 
        reverse=True
    )
    
    # Likely: Sort by weighted score (incorporates discovery_score for experienced users)
    likely_milestones.sort(
        key=lambda x: calculate_weighted_score(x, 'likely', discovery_weight), 
        reverse=True
    )
    
    # Challenge: Sort by weighted score, then by mastery_age (closest future first)
    challenge_milestones.sort(
        key=lambda x: (
            calculate_weighted_score(x, 'challenge', discovery_weight), 
            -x.get('mastery_age', 999)
        ), 
        reverse=True
    )
    
    # Select one from each category, ensuring diversity across domains
    recommendations = []
    selected_domains = set()
    selected_ids = set()
    
    # Reorder selection priority based on baby's proficiency:
    # - If proficient: Prioritize Likely and Challenge, skip or minimize Foundational
    # - If not proficient: Traditional order (Foundational, Likely, Challenge)
    
    if restrict_foundational:
        # Baby has shown proficiency: prioritize age-appropriate and future milestones
        # 1. Likely (age-appropriate) - natural next step
        if likely_milestones:
            add_milestone_with_diversity_check(
                likely_milestones, recommendations, selected_ids, selected_domains
            )
        
        # 2. Challenge (future age) - advanced milestone
        if challenge_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(
                challenge_milestones, recommendations, selected_ids, selected_domains
            )
        
        # 3. Foundational (past age, but only very recent ones) - only if we need more
        if foundational_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(
                foundational_milestones, recommendations, selected_ids, selected_domains
            )
    else:
        # Traditional order: Foundational, Likely, Challenge
        # 1. Foundational (past age) - prioritize catching up
        if foundational_milestones:
            add_milestone_with_diversity_check(
                foundational_milestones, recommendations, selected_ids, selected_domains
            )
        
        # 2. Likely (high probability) - natural next step
        if likely_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(
                likely_milestones, recommendations, selected_ids, selected_domains
            )
        
        # 3. Challenge (future age) - advanced milestone
        if challenge_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(
                challenge_milestones, recommendations, selected_ids, selected_domains
            )
    
    # If we have less than 3, fill with best remaining from any category
    # Still prioritize domain diversity, but favor milestones at/above age if baby is proficient
    if len(recommendations) < 3:
        all_remaining = foundational_milestones + likely_milestones + challenge_milestones
        # Remove already selected
        all_remaining = [m for m in all_remaining if m['milestone_id'] not in selected_ids]
        
        # Sort by combined score for remaining, with age-based priority if proficient
        for milestone in all_remaining:
            if milestone['mastery_age'] is not None:
                if restrict_foundational and milestone['age_difference'] > 1.0:
                    # Baby is proficient: strongly penalize milestones that are too far in the past
                    # Prefer milestones at or above baby's age
                    age_penalty = max(0, (milestone['age_difference'] - 1.0) * 0.5)  # Penalty for being too far past
                    if milestone['age_difference'] > 0:
                        combined = (milestone['foundation_score'] * 0.5 + milestone['transition_probability'] * 0.3) - age_penalty
                    else:
                        # Future milestones get a boost when baby is proficient
                        category = milestone.get('category', 'likely')
                        combined = calculate_weighted_score(milestone, category, discovery_weight) + 0.2
                elif milestone['age_difference'] > 0:
                    combined = milestone['foundation_score'] * 0.7 + milestone['transition_probability'] * 0.3
                else:
                    # Apply dynamic weighting for likely/challenge
                    category = milestone.get('category', 'likely')
                    combined = calculate_weighted_score(milestone, category, discovery_weight)
            else:
                combined = milestone['transition_probability'] * 0.7 + milestone['discovery_score'] * 0.3
            milestone['combined_score'] = combined
        
        # Sort by combined score, but if proficient, also prioritize by mastery_age (higher = better)
        if restrict_foundational:
            all_remaining.sort(
                key=lambda x: (
                    x.get('combined_score', 0),
                    -x.get('mastery_age', 0)  # Prefer milestones at/above current age
                ),
                reverse=True
            )
        else:
            all_remaining.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Add until we have 3, still checking for diversity
        # When baby is proficient, skip milestones that are too far in the past
        for milestone in all_remaining:
            if len(recommendations) >= 3:
                break
            
            # If baby is proficient, skip milestones that are too young (more than 2 months below baby's age)
            if restrict_foundational and milestone.get('mastery_age') is not None:
                if milestone['mastery_age'] < min_allowed_mastery_age:
                    continue  # Skip milestones that are too young
                # Also skip foundational milestones that are too far in the past (> 1 month)
                if milestone.get('category') == 'foundational' and milestone.get('age_difference', 0) > max_foundational_age_diff:
                    continue  # Skip milestones that are too young
            
            milestone_domain = milestone.get('domain', 'unknown')
            # Prefer milestones from unrepresented domains
            if milestone_domain not in selected_domains or len(selected_domains) >= 3:
                recommendations.append(milestone)
                selected_ids.add(milestone['milestone_id'])
                selected_domains.add(milestone_domain)
            elif len([m for m in all_remaining if m.get('domain') not in selected_domains]) == 0:
                # If no other domains available, add this one (but still check age restriction)
                if restrict_foundational and milestone.get('mastery_age') is not None:
                    if milestone['mastery_age'] < min_allowed_mastery_age:
                        continue  # Skip milestones that are too young
                    if milestone.get('category') == 'foundational' and milestone.get('age_difference', 0) > max_foundational_age_diff:
                        continue  # Skip foundational milestones that are too far in the past
                recommendations.append(milestone)
                selected_ids.add(milestone['milestone_id'])
    
    # Limit to top 3 and ensure no duplicates
    seen_ids = set()
    unique_recommendations = []
    for rec in recommendations[:3]:
        if rec['milestone_id'] not in seen_ids and rec['milestone_id'] not in completed_set:
            unique_recommendations.append(rec)
            seen_ids.add(rec['milestone_id'])
    recommendations = unique_recommendations
    
    # Final filter: only include milestones with activities AND ensure strict exclusion of completed milestones
    if available_milestone_ids is not None:
        recommendations = [
            rec for rec in recommendations 
            if rec['milestone_id'] in available_milestone_ids 
            and rec['milestone_id'] not in completed_set  # Final exclusion check
        ]
    
    # Ensure recommendations is initialized (in case frontier_scores was empty)
    if 'recommendations' not in locals():
        recommendations = []
    
    # Format results with human-readable names
    formatted_recommendations = []
    for item in recommendations:
        # Final safety check: If baby is proficient, ensure no milestones are too young
        if restrict_foundational and item.get('mastery_age') is not None:
            if min_allowed_mastery_age is not None and item['mastery_age'] < min_allowed_mastery_age:
                continue  # Skip milestones that are too young
        
        formatted_recommendations.append({
            'milestone_id': item['milestone_id'],
            'milestone_name': milestone_map.get(item['milestone_id'], 'Unknown milestone'),
            'probability': round(item['transition_probability'], 4),
            'discovery_score': round(item['discovery_score'], 4),
            'foundation_score': round(item['foundation_score'], 2),  # Renamed from urgency_score
            'category': item.get('category', 'unknown'),
            'mastery_age': item['mastery_age']
        })
    
    # Fallback: If fewer than 3 recommendations found, try age-based recommendations with progressively relaxed bounds
    # This ensures users always get suggestions even if transition-based logic runs out
    if len(formatted_recommendations) < 3:
        completed_set = set(user_completed_ids)
        num_needed = 3 - len(formatted_recommendations)
        existing_ids = {rec['milestone_id'] for rec in formatted_recommendations}
        
        print(f"⚠ Only {len(formatted_recommendations)} transition-based recommendations found. Trying fallback for {num_needed} more.")
        
        # Try progressively relaxed age bounds until we find enough recommendations
        age_bound_steps = [
            (3.0, 0.5),   # Standard: 3 months past/future, 0.5 month tolerance
            (6.0, 1.0),   # Relaxed: 6 months past/future, 1.0 month tolerance  
            (12.0, 2.0),  # Very relaxed: 12 months past/future, 2.0 month tolerance
            (24.0, 6.0),  # Extended: 24 months past/future, 6.0 month tolerance
            (48.0, 12.0)  # Maximum: Any milestone in 0-48 month range
        ]
        
        # Determine if we should restrict past-age recommendations based on proficiency
        # If baby has completed milestones, check their proficiency level
        restrict_past = restrict_foundational  # Use the same proficiency check from main logic
        min_allowed_age_for_fallback = min_allowed_mastery_age if restrict_past else None
        
        for age_bound, tolerance in age_bound_steps:
            age_based_recs = _get_age_based_recommendations(
                baby_age_months, mastery_ages, milestone_map, csv_file, 
                available_milestone_ids, age_bound=age_bound, tolerance=tolerance,
                restrict_past_age=restrict_past
            )
            
            # Filter out completed milestones, already recommended ones, and too-young milestones if proficient
            age_based_recs = [
                rec for rec in age_based_recs 
                if rec['milestone_id'] not in completed_set
                and rec['milestone_id'] not in existing_ids
                and (min_allowed_age_for_fallback is None or rec.get('mastery_age') is None or rec['mastery_age'] >= min_allowed_age_for_fallback)
            ]
            
            if age_based_recs:
                print(f"✓ Found {len(age_based_recs)} age-based recommendations (bound={age_bound}mo, tolerance={tolerance}mo)")
                # Add the new recommendations to existing ones (up to 3 total)
                formatted_recommendations.extend(age_based_recs[:num_needed])
                if len(formatted_recommendations) >= 3:
                    break  # We have enough, stop trying more relaxed bounds
        
        # If still not enough and we're running out of milestones with activities,
        # try using ALL milestones from dataset (even without activities) as last resort
        if len(formatted_recommendations) < 3 and available_milestone_ids:
            completed_count = len([m for m in completed_set if m in available_milestone_ids])
            completion_rate = completed_count / len(available_milestone_ids) if available_milestone_ids else 0
            
            if completion_rate >= 0.7:  # 70% or more of available milestones completed
                print(f"⚠ {completion_rate:.0%} of available milestones completed. Expanding to full dataset as last resort.")
                existing_ids = {rec['milestone_id'] for rec in formatted_recommendations}
                num_needed = 3 - len(formatted_recommendations)
                
                # Use full dataset with very relaxed bounds to find any remaining milestones
                # Exclude completed milestones during selection, not just after
                # Use the same proficiency check from main logic
                restrict_past = restrict_foundational
                min_allowed_age_for_fallback = min_allowed_mastery_age if restrict_past else None
                
                age_based_recs = _get_age_based_recommendations(
                    baby_age_months, mastery_ages, milestone_map, csv_file, 
                    available_milestone_ids=None, age_bound=48.0, tolerance=12.0, 
                    max_results=15, exclude_ids=completed_set, restrict_past_age=restrict_past
                )
                
                # Filter out already recommended milestones (completed are already excluded)
                # Also filter out too-young milestones if baby is proficient
                age_based_recs = [
                    rec for rec in age_based_recs 
                    if rec['milestone_id'] not in existing_ids
                    and rec['milestone_id'] in milestone_map  # Ensure we have a name for it
                    and (min_allowed_age_for_fallback is None or rec.get('mastery_age') is None or rec['mastery_age'] >= min_allowed_age_for_fallback)
                ]
                
                if age_based_recs:
                    print(f"✓ Found {len(age_based_recs)} recommendations from full dataset (may lack activities)")
                    # If we still need more, try getting additional recommendations by calling the function again
                    # with a request for more results (we'll modify the function to return more if needed)
                    formatted_recommendations.extend(age_based_recs[:num_needed])
                    
                    # If we still don't have enough, try to get more by being less selective
                    if len(formatted_recommendations) < 3 and len(age_based_recs) > num_needed:
                        # Use the remaining ones we already found
                        additional_needed = 3 - len(formatted_recommendations)
                        formatted_recommendations.extend(age_based_recs[num_needed:num_needed + additional_needed])
    
    return formatted_recommendations[:3]  # Return up to 3 total recommendations


def _calculate_milestone_frequencies(csv_file):
    """
    Calculate frequency (count of non-missing observations) for each milestone.
    
    Args:
        csv_file: Path to processed milestones CSV file
    
    Returns:
        dict: Dictionary mapping milestone IDs to their frequency counts
    """
    if not Path(csv_file).exists():
        raise FileNotFoundError(
            f"CSV file not found: {csv_file}. "
            "Required for new user recommendations."
        )
    
    df = pd.read_csv(csv_file)
    milestone_cols = get_milestone_columns(df)
    
    frequencies = {}
    for col in milestone_cols:
        # Count non-missing values (not -1)
        count = (df[col] != -1).sum()
        frequencies[col] = count
    
    return frequencies


def _get_age_based_recommendations(baby_age_months, mastery_ages, milestone_map, csv_file, available_milestone_ids=None, age_bound=3.0, tolerance=0.5, max_results=10, exclude_ids=None, restrict_past_age=False):
    """
    Get recommendations for new users based on baby's age and milestone frequency.
    
    Ensures a balanced mix: 1 Foundational (past age), 1 Likely (high frequency), 1 Challenge (future age).
    When restrict_past_age is True, prioritizes milestones at or above baby's age.
    
    Args:
        baby_age_months: Current age of the baby in months
        mastery_ages: Dictionary of milestone -> mastery age
        milestone_map: Dictionary of milestone -> human-readable name
        csv_file: Path to CSV file for frequency calculation
        available_milestone_ids: Set of milestone IDs that have activities (for filtering)
        age_bound: Maximum months past/future to consider (default: 3.0)
        tolerance: Age difference tolerance for "likely" category (default: 0.5)
        max_results: Maximum number of recommendations to return (default: 10, for filtering flexibility)
        exclude_ids: Set of milestone IDs to exclude (e.g., already completed milestones)
        restrict_past_age: If True, restrict foundational milestones to only those very close to current age
    
    Returns:
        List of up to max_results recommendation dictionaries (default 10 to allow filtering)
    """
    # Calculate milestone frequencies
    frequencies = _calculate_milestone_frequencies(csv_file)
    max_frequency = max(frequencies.values()) if frequencies else 1
    
    # Filter milestones to only include those with activities (if specified)
    if available_milestone_ids is not None:
        mastery_ages = {
            mid: age for mid, age in mastery_ages.items() 
            if mid in available_milestone_ids
        }
    
    # Exclude completed milestones if provided
    exclude_set = exclude_ids if exclude_ids is not None else set()
    mastery_ages = {
        mid: age for mid, age in mastery_ages.items()
        if mid not in exclude_set
    }
    
    # Categorize milestones
    foundational_milestones = []
    likely_milestones = []
    challenge_milestones = []
    
    for milestone_id, mastery_age in mastery_ages.items():
        if mastery_age is None:
            continue
        
        frequency = frequencies.get(milestone_id, 0)
        normalized_probability = frequency / max_frequency if max_frequency > 0 else 0
        discovery_score = 1.0 - normalized_probability
        
        age_difference = baby_age_months - mastery_age
        
        milestone_info = {
            'milestone_id': milestone_id,
            'mastery_age': mastery_age,
            'frequency': frequency,
            'normalized_probability': normalized_probability,
            'discovery_score': discovery_score,
            'age_difference': age_difference,
            'foundation_score': min(max(0, age_difference), 12.0) / 12.0 if age_difference > 0 else 0.0
        }
        
        # Add domain info
        milestone_info['domain'] = get_milestone_domain(milestone_id)
        
        # Categorize with configurable age bounds:
        # - Foundational: Past age but not more than age_bound months behind
        # - Likely: Age-appropriate (within tolerance months of baby's age)
        # - Challenge: Near future, within age_bound months ahead
        # When restrict_past_age is True, never recommend milestones significantly below baby's age
        
        # First check: If restricting past age, skip milestones that are too young (more than 2 months below)
        if restrict_past_age and mastery_age < (baby_age_months - 2.0):
            continue  # Skip milestones that are too young
        
        if age_difference > tolerance and age_difference <= age_bound:
            # Foundational: Baby is past the typical mastery age, but within age_bound
            # If restricting past age, only include if very close (within 1 month)
            if restrict_past_age:
                if age_difference <= 1.0:
                    milestone_info['category'] = 'foundational'
                    foundational_milestones.append(milestone_info)
                # If too far in the past, treat as likely if close enough
                elif abs(age_difference) <= 1.5:
                    milestone_info['category'] = 'likely'
                    likely_milestones.append(milestone_info)
                # Skip milestones that are too far in the past
            else:
                milestone_info['category'] = 'foundational'
                foundational_milestones.append(milestone_info)
        elif age_difference < -tolerance and age_difference >= -age_bound:
            # Challenge: Milestone is in the near future (within age_bound)
            milestone_info['category'] = 'challenge'
            challenge_milestones.append(milestone_info)
        elif abs(age_difference) <= tolerance:
            # Likely: Age-appropriate (within tolerance of current age)
            milestone_info['category'] = 'likely'
            likely_milestones.append(milestone_info)
        # Ignore milestones that are too far outside the age_bound
    
    # Sort each category
    # Foundational: Sort by mastery_age (most recent first, i.e., closest to baby's age), then by frequency
    foundational_milestones.sort(key=lambda x: (x['mastery_age'], x['frequency']), reverse=True)
    
    # Likely: Sort by frequency (highest first), then by age difference (closest first)
    likely_milestones.sort(key=lambda x: (x['frequency'], -abs(x['age_difference'])), reverse=True)
    
    # Challenge: Sort by mastery_age (closest future first, i.e., lowest mastery_age), then by frequency
    challenge_milestones.sort(key=lambda x: (-x['mastery_age'], x['frequency']), reverse=True)
    
    # Select one from each category to ensure diversity across domains
    recommendations = []
    selected_domains = set()
    selected_ids = set()
    
    def add_milestone_with_diversity_check(milestone_list, category_name):
        """Try to add a milestone from the list, prioritizing domain diversity."""
        for milestone in milestone_list:
            if milestone['milestone_id'] in selected_ids:
                continue
            
            milestone_domain = milestone.get('domain', 'unknown')
            
            # If we need diversity (have 1+ recommendations), prioritize different domains
            if len(recommendations) >= 1:
                # If this domain is already represented, skip unless it's the last option
                if milestone_domain in selected_domains:
                    # Check if there's a different domain available
                    available_different_domains = [
                        m for m in milestone_list 
                        if m['milestone_id'] not in selected_ids 
                        and m.get('domain') not in selected_domains
                    ]
                    if available_different_domains:
                        continue  # Skip this one, we'll get a different domain later
            
            # Add this milestone
            recommendations.append(milestone)
            selected_ids.add(milestone['milestone_id'])
            selected_domains.add(milestone_domain)
            return True
        return False
    
    # Reorder selection priority if restricting past age (prioritize age-appropriate and future)
    if restrict_past_age:
        # 1. Likely (age-appropriate, high frequency) - prioritize these
        if likely_milestones:
            add_milestone_with_diversity_check(likely_milestones, 'likely')
        
        # 2. Challenge (future age) - advanced milestones
        if challenge_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(challenge_milestones, 'challenge')
        
        # 3. Foundational (past age, but only very recent ones) - only if we need more
        if foundational_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(foundational_milestones, 'foundational')
    else:
        # Traditional order: Foundational, Likely, Challenge
        # 1. Foundational (past age)
        if foundational_milestones:
            add_milestone_with_diversity_check(foundational_milestones, 'foundational')
        
        # 2. Likely (age-appropriate, high frequency)
        if likely_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(likely_milestones, 'likely')
        
        # 3. Challenge (future age)
        if challenge_milestones and len(recommendations) < 3:
            add_milestone_with_diversity_check(challenge_milestones, 'challenge')
    
    # If we have less than 3, fill with best remaining from any category
    # Still prioritize domain diversity
    if len(recommendations) < 3:
        all_remaining = foundational_milestones + likely_milestones + challenge_milestones
        all_remaining = [m for m in all_remaining if m['milestone_id'] not in selected_ids]
        
        # Sort by combined score, prioritizing milestones at/above age if restricting past age
        for milestone in all_remaining:
            if restrict_past_age and milestone['age_difference'] > 1.0:
                # Penalize milestones that are too far in the past
                age_penalty = (milestone['age_difference'] - 1.0) * 0.5
                if milestone['age_difference'] > 0:
                    combined = (milestone['foundation_score'] * 0.5 + milestone['normalized_probability'] * 0.3) - age_penalty
                else:
                    combined = milestone['normalized_probability'] * 0.5 + milestone['discovery_score'] * 0.5 + 0.2  # Boost future milestones
            elif milestone['age_difference'] > 0:
                combined = milestone['foundation_score'] * 0.7 + milestone['normalized_probability'] * 0.3
            else:
                combined = milestone['normalized_probability'] * 0.5 + milestone['discovery_score'] * 0.5
            milestone['combined_score'] = combined
        
        # Sort by score, but if restricting past age, also prioritize by mastery_age
        if restrict_past_age:
            all_remaining.sort(
                key=lambda x: (
                    x.get('combined_score', 0),
                    -x.get('mastery_age', 0)  # Prefer milestones at/above current age
                ),
                reverse=True
            )
        else:
            all_remaining.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Add until we have 3, still checking for diversity
        for milestone in all_remaining:
            if len(recommendations) >= 3:
                break
            
            # If restricting past age, skip milestones that are too young (more than 2 months below baby's age)
            if restrict_past_age and milestone.get('mastery_age') is not None:
                if milestone['mastery_age'] < (baby_age_months - 2.0):
                    continue  # Skip milestones that are too young
                # Also skip foundational milestones that are too far in the past (> 1 month)
                if milestone.get('category') == 'foundational' and milestone['age_difference'] > 1.0:
                    continue
            
            milestone_domain = milestone.get('domain', 'unknown')
            # Prefer milestones from unrepresented domains
            if milestone_domain not in selected_domains or len(selected_domains) >= 3:
                recommendations.append(milestone)
                selected_ids.add(milestone['milestone_id'])
                selected_domains.add(milestone_domain)
            elif len([m for m in all_remaining if m.get('domain') not in selected_domains]) == 0:
                # If no other domains available, add this one (but still check age restriction)
                if restrict_past_age and milestone.get('mastery_age') is not None:
                    if milestone['mastery_age'] < (baby_age_months - 2.0):
                        continue  # Skip milestones that are too young
                    if milestone.get('category') == 'foundational' and milestone['age_difference'] > 1.0:
                        continue  # Skip foundational milestones that are too far in the past
                recommendations.append(milestone)
                selected_ids.add(milestone['milestone_id'])
    
    # Limit to max_results and ensure uniqueness
    seen_ids = set()
    unique_recommendations = []
    for rec in recommendations[:max_results]:
        if rec['milestone_id'] not in seen_ids:
            unique_recommendations.append(rec)
            seen_ids.add(rec['milestone_id'])
    recommendations = unique_recommendations
    
    if available_milestone_ids is not None:
        recommendations = [
            rec for rec in recommendations 
            if rec['milestone_id'] in available_milestone_ids
        ]
    
    # Format results
    formatted_recommendations = []
    for item in recommendations:
        # Final safety check: If restricting past age, ensure no milestones are too young
        if restrict_past_age and item.get('mastery_age') is not None:
            if item['mastery_age'] < (baby_age_months - 2.0):
                continue  # Skip milestones that are too young
        
        formatted_recommendations.append({
            'milestone_id': item['milestone_id'],
            'milestone_name': milestone_map.get(item['milestone_id'], 'Unknown milestone'),
            'probability': round(item['normalized_probability'], 4),
            'discovery_score': round(item['discovery_score'], 4),
            'foundation_score': round(item['foundation_score'], 2),
            'category': item.get('category', 'unknown'),
            'mastery_age': item['mastery_age']
        })
    
    return formatted_recommendations

