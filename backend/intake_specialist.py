"""
NextPlay Intake Specialist
Extracts structured developmental data from a parent's casual description of their child.
Uses OpenAI API for natural language understanding.
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not installed. Install with: pip install openai")


class IntakeSpecialist:
    """Extracts structured developmental data from natural language input using OpenAI."""
    
    def __init__(self, milestone_map: Dict[str, str], openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the intake specialist with milestone mapping.
        
        Args:
            milestone_map: Dictionary mapping milestone codes to descriptions
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
            model: OpenAI model to use (default: "gpt-4o-mini")
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is required. Install with: pip install openai")
        
        self.milestone_map = milestone_map
        self.model = model
        
        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        
        # Create milestone reference text for the prompt
        self.milestone_reference = self._create_milestone_reference()
    
    def _create_milestone_reference(self) -> str:
        """Create a formatted string of all milestones for the prompt."""
        lines = []
        for code, description in sorted(self.milestone_map.items()):
            lines.append(f"- {code}: {description}")
        return "\n".join(lines)
    
    def _create_extraction_prompt(self, user_input: str) -> str:
        """Create the prompt for OpenAI to extract structured data."""
        prompt = f"""You are the NextPlay Intake Specialist. Your goal is to extract structured developmental data from a parent's casual description of their child.

INPUT: "{user_input}"

REFERENCE DATA - Available GSED Milestone Codes and Descriptions:
{self.milestone_reference}

EXTRACTION RULES:

1. Age: Extract the age in months. If the parent provides years, multiply by 12. If the age is ambiguous (e.g., 'almost 1', 'nearly 2', 'about 6 months'), return null.
   IMPORTANT: When you see "18 months", "18 month old", or "18-month-old", extract it as 18.0 (not 1.8). 
   Common patterns:
   - "6 months" = 6.0
   - "18 months" = 18.0 (NOT 1.8)
   - "1 year" = 12.0
   - "1.5 years" = 18.0
   - "18 month old" = 18.0

2. Child Name: Extract the child's name if mentioned. Common patterns: "my baby [name]", "my child [name]", "[name] is...". If not found, return null.

3. Completed Milestones: Identify any milestones the parent explicitly mentions the child can do. Map these to the most likely GSED codes from the reference list above. Only include milestones with 80%+ certainty. Do not guess or infer milestones that aren't clearly mentioned. If no milestones are clearly identified, return an empty array.

4. Needs Clarification: Set to true only if age_months is null (ambiguous or missing age). Otherwise false.

5. Follow-up Question: If needs_clarification is true, use: "Your baby sounds wonderful! To give you the best recommendations, exactly how many months old are they?" Otherwise null.

Return ONLY valid JSON matching this exact schema:
{{
  "child_name": string | null,
  "age_months": number | null,
  "completed_milestone_ids": string[],
  "needs_clarification": boolean,
  "follow_up_question": string | null
}}

IMPORTANT: 
- Return ONLY the JSON object, no additional text or explanation
- milestone codes must match exactly from the reference list (e.g., "ddigmd063")
- age_months must be a number (float) or null
- completed_milestone_ids must be an array of strings (milestone codes) or empty array
- Only include milestones that are explicitly mentioned in the input
- Be conservative - only map milestones if you're highly confident (80%+ certainty)"""
        
        return prompt
    
    def process_intake(self, text: str) -> Dict:
        """
        Process a parent's intake description and return structured data using OpenAI.
        
        Args:
            text: Natural language description from parent
            
        Returns:
            Dictionary matching the JSON schema:
            {
                "child_name": string | null,
                "age_months": number | null,
                "completed_milestone_ids": string[],
                "needs_clarification": boolean,
                "follow_up_question": string | null
            }
        """
        try:
            # Create the extraction prompt
            prompt = self._create_extraction_prompt(text)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from natural language and returns only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Extract and parse JSON from response
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON (handle if wrapped in code blocks)
            if response_text.startswith("```"):
                # Remove code block markers
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Validate and normalize the result
            # Ensure milestone_ids are valid and exist in milestone_map
            if "completed_milestone_ids" in result:
                valid_milestone_ids = [
                    code for code in result["completed_milestone_ids"]
                    if code in self.milestone_map
                ]
                result["completed_milestone_ids"] = valid_milestone_ids
            
            # Ensure needs_clarification is set correctly based on age_months
            if result.get("age_months") is None:
                result["needs_clarification"] = True
                if not result.get("follow_up_question"):
                    result["follow_up_question"] = "Your baby sounds wonderful! To give you the best recommendations, exactly how many months old are they?"
            else:
                result["needs_clarification"] = False
                result["follow_up_question"] = None
            
            # Ensure types are correct
            if result.get("age_months") is not None:
                result["age_months"] = float(result["age_months"])
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Error calling OpenAI API: {e}")


def load_intake_specialist(milestone_map_file: Optional[str] = None, 
                          openai_api_key: Optional[str] = None,
                          model: str = "gpt-4o-mini") -> IntakeSpecialist:
    """
    Load the intake specialist with milestone data.
    
    Args:
        milestone_map_file: Path to milestone map JSON file (defaults to config.MILESTONE_MAP_JSON)
        openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        model: OpenAI model to use (default: "gpt-4o-mini")
        
    Returns:
        Initialized IntakeSpecialist instance
    """
    from config import MILESTONE_MAP_JSON
    
    milestone_map_path = Path(milestone_map_file or str(MILESTONE_MAP_JSON))
    if not milestone_map_path.exists():
        raise FileNotFoundError(f"Milestone map file not found: {milestone_map_path}")
    
    with open(milestone_map_path, 'r', encoding='utf-8') as f:
        milestone_map = json.load(f)
    
    return IntakeSpecialist(milestone_map, openai_api_key=openai_api_key, model=model)

