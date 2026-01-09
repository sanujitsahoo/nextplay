"""
Utility functions for NextPlay recommendation engine.

This module provides shared helper functions used across the recommendation system,
including milestone categorization, domain extraction, and diversity filtering.
"""

from typing import Dict, List, Set, Tuple, Optional
from config import (
    FOUNDATIONAL_AGE_BOUND,
    LIKELY_AGE_TOLERANCE,
    CHALLENGE_AGE_BOUND,
    MAX_URGENCY_AGE_DIFF,
    DOMAIN_MAPPING
)


def get_milestone_domain(milestone_id: str) -> str:
    """
    Extract the developmental domain from a milestone ID.
    
    GSED milestone codes follow the pattern: ddi[domain][type][number]
    where domain is:
    - 'c' = Cognitive
    - 'f' = Fine Motor
    - 'g' = Gross Motor
    
    Args:
        milestone_id: Milestone code (e.g., 'ddigmd055', 'ddicmm030')
    
    Returns:
        Domain string: 'cognitive', 'fine_motor', 'gross_motor', or 'unknown'
    
    Example:
        >>> get_milestone_domain('ddigmd055')
        'gross_motor'
        >>> get_milestone_domain('ddicmm030')
        'cognitive'
    """
    if len(milestone_id) > 3:
        domain_char = milestone_id[3].lower()
        return DOMAIN_MAPPING.get(domain_char, 'unknown')
    return 'unknown'


def categorize_milestone_by_age(age_difference: float) -> Optional[str]:
    """
    Categorize a milestone based on the difference between baby's age and mastery age.
    
    Categories:
    - 'foundational': Past age but within reasonable bounds (needs to catch up)
    - 'likely': Age-appropriate (natural next step)
    - 'challenge': Future milestone (advanced development)
    
    Args:
        age_difference: baby_age_months - mastery_age (positive = past, negative = future)
    
    Returns:
        Category string or None if milestone is outside reasonable bounds
    
    Example:
        >>> categorize_milestone_by_age(2.0)  # 2 months past
        'foundational'
        >>> categorize_milestone_by_age(0.2)  # Age-appropriate
        'likely'
        >>> categorize_milestone_by_age(-1.5)  # 1.5 months future
        'challenge'
    """
    if age_difference > 0 and age_difference <= FOUNDATIONAL_AGE_BOUND:
        return 'foundational'
    elif age_difference < -LIKELY_AGE_TOLERANCE and age_difference >= -CHALLENGE_AGE_BOUND:
        return 'challenge'
    elif abs(age_difference) <= LIKELY_AGE_TOLERANCE:
        return 'likely'
    return None  # Outside reasonable bounds


def calculate_urgency_score(age_difference: float) -> float:
    """
    Calculate urgency score for a milestone based on age difference.
    
    Urgency score is normalized to 0-1 range, where:
    - 0 = no urgency (future milestone or just achieved)
    - 1 = maximum urgency (12+ months past typical age)
    
    Args:
        age_difference: baby_age_months - mastery_age (positive = past, negative = future)
    
    Returns:
        Urgency score between 0.0 and 1.0
    
    Example:
        >>> calculate_urgency_score(6.0)  # 6 months past
        0.5
        >>> calculate_urgency_score(-2.0)  # Future milestone
        0.0
    """
    if age_difference <= 0:
        return 0.0
    # Normalize: cap at MAX_URGENCY_AGE_DIFF months
    normalized = min(max(0, age_difference), MAX_URGENCY_AGE_DIFF) / MAX_URGENCY_AGE_DIFF
    return normalized


def add_milestone_with_diversity_check(
    milestone_list: List[Dict],
    recommendations: List[Dict],
    selected_ids: Set[str],
    selected_domains: Set[str]
) -> bool:
    """
    Add a milestone from the list to recommendations, ensuring domain diversity.
    
    This function prioritizes milestones from unrepresented domains to ensure
    a balanced set of recommendations across developmental areas (Cognitive,
    Fine Motor, Gross Motor).
    
    Args:
        milestone_list: List of milestone dictionaries to choose from
        recommendations: Current list of recommendations (modified in-place)
        selected_ids: Set of already selected milestone IDs
        selected_domains: Set of already represented domains
    
    Returns:
        True if a milestone was added, False otherwise
    
    Example:
        >>> milestones = [{'milestone_id': 'ddigmd055', 'domain': 'gross_motor'}]
        >>> recs = []
        >>> selected = set()
        >>> domains = set()
        >>> add_milestone_with_diversity_check(milestones, recs, selected, domains)
        True
    """
    for milestone in milestone_list:
        milestone_id = milestone.get('milestone_id')
        if milestone_id in selected_ids:
            continue
        
        milestone_domain = milestone.get('domain', 'unknown')
        
        # If we need diversity (have 1+ recommendations), prioritize different domains
        if len(recommendations) >= 1:
            # If this domain is already represented, skip unless it's the last option
            if milestone_domain in selected_domains:
                # Check if there's a different domain available
                available_different_domains = [
                    m for m in milestone_list 
                    if m.get('milestone_id') not in selected_ids 
                    and m.get('domain') not in selected_domains
                ]
                if available_different_domains:
                    continue  # Skip this one, we'll get a different domain later
        
        # Add this milestone
        recommendations.append(milestone)
        selected_ids.add(milestone_id)
        selected_domains.add(milestone_domain)
        return True
    return False


def calculate_weighted_score(
    milestone: Dict,
    category: str,
    discovery_weight: float
) -> float:
    """
    Calculate weighted score for a milestone based on category and discovery weight.
    
    For 'likely' and 'challenge' categories, incorporates discovery_score to
    surface rarer/advanced milestones. For 'foundational', uses transition
    probability only.
    
    Args:
        milestone: Milestone dictionary with 'transition_probability' and 'discovery_score'
        category: Category string ('foundational', 'likely', 'challenge')
        discovery_weight: Weight for discovery_score (0.2 for base, 0.4 for level-up)
    
    Returns:
        Weighted score (higher = better)
    
    Example:
        >>> milestone = {'transition_probability': 0.7, 'discovery_score': 0.3}
        >>> calculate_weighted_score(milestone, 'likely', 0.2)
        0.76
    """
    base_score = milestone.get('transition_probability', 0.0)
    
    if category in ('likely', 'challenge'):
        discovery_boost = milestone.get('discovery_score', 0.0) * discovery_weight
        return base_score + discovery_boost
    
    return base_score


def filter_available_milestones(
    milestones: List[Dict],
    available_milestone_ids: Optional[Set[str]],
    completed_ids: Set[str]
) -> List[Dict]:
    """
    Filter milestones to only include those with activities and exclude completed ones.
    
    Args:
        milestones: List of milestone dictionaries
        available_milestone_ids: Set of milestone IDs that have activities (None = no filter)
        completed_ids: Set of completed milestone IDs to exclude
    
    Returns:
        Filtered list of milestones
    """
    filtered = [
        m for m in milestones
        if m.get('milestone_id') not in completed_ids
    ]
    
    if available_milestone_ids is not None:
        filtered = [
            m for m in filtered
            if m.get('milestone_id') in available_milestone_ids
        ]
    
    return filtered

