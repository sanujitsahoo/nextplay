"""
NextPlay FastAPI Application
Baby development milestone recommendation engine with play activities.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
import os
import traceback
from pathlib import Path
from dotenv import load_dotenv

import engine_logic
import recommender
import intake_specialist
from config import (
    BASE_DIR,
    ALLOWED_ORIGINS,
    VERCEL_ORIGIN_REGEX,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    PROCESSED_CSV,
    MASTERY_AGES_JSON,
    TRANSITION_MATRIX_JSON,
    MILESTONE_MAP_JSON,
    ACTIVITIES_JSON,
    ENV_OPENAI_API_KEY,
    ENV_OPENAI_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_ENCODING
)

# Load environment variables from .env file
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded environment variables from {env_path}")
else:
    print(f"⚠ No .env file found at {env_path}. Using system environment variables.")

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# CORS Configuration
# Allow origins for development (localhost) and production (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=VERCEL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Global variables to store loaded data (initialized on startup)
mastery_ages: Dict[str, Optional[float]] = {}
transition_matrix: Dict[str, List] = {}
activities_map: Dict[str, Dict] = {}
milestone_map: Dict[str, str] = {}
intake_specialist_instance: Optional[intake_specialist.IntakeSpecialist] = None

class RecommendationRequest(BaseModel):
    """Request model for recommendation endpoint."""
    baby_age_months: float = Field(..., ge=0, description="Baby's current age in months")
    completed_milestone_ids: List[str] = Field(default_factory=list, description="List of completed milestone IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "baby_age_months": 6.0,
                "completed_milestone_ids": ["ddicmm029", "ddicmm030", "ddigmd055"]
            }
        }

class RecommendationResponse(BaseModel):
    """Response model for recommendation endpoint."""
    recommendations: List[dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "milestone_id": "ddigmd063",
                        "milestone_name": "Sits in stable position without support",
                        "probability": 0.75,
                        "discovery_score": 0.25,
                        "foundation_score": 0.0,
                        "category": "likely",
                        "mastery_age": 6.5,
                        "activity": {
                            "title": "Independent Sitter",
                            "materials": ["toys"],
                            "instructions": [
                                "Sit your baby on the floor without support...",
                                "Encourage reaching for toys..."
                            ],
                            "benefit": "Science Tip: Unassisted sitting requires..."
                        }
                    }
                ]
            }
        }

@app.on_event("startup")
async def load_data():
    """Load all required data files on application startup using relative paths."""
    global mastery_ages, transition_matrix, activities_map, milestone_map
    
    print(f"Loading NextPlay data files from {BASE_DIR}...")
    
    # Load mastery ages
    try:
        mastery_ages = engine_logic.load_mastery_ages(str(MASTERY_AGES_JSON))
        print(f"✓ Loaded mastery_ages.json ({len(mastery_ages)} milestones)")
    except FileNotFoundError:
        print(f"⚠ Warning: mastery_ages.json not found at {MASTERY_AGES_JSON}")
        mastery_ages = {}
    
    # Load transition matrix
    try:
        transition_matrix = engine_logic.load_transition_matrix(str(TRANSITION_MATRIX_JSON))
        print(f"✓ Loaded transition_matrix.json ({len(transition_matrix)} milestones)")
    except FileNotFoundError:
        print(f"⚠ Warning: transition_matrix.json not found at {TRANSITION_MATRIX_JSON}")
        transition_matrix = {}
    
    # Load milestone map
    milestone_map = engine_logic.load_milestone_map(str(MILESTONE_MAP_JSON))
    if milestone_map:
        print(f"✓ Loaded milestone_map.json ({len(milestone_map)} entries)")
    
    # Initialize intake specialist
    try:
        openai_api_key = os.getenv(ENV_OPENAI_API_KEY)
        if openai_api_key:
            intake_specialist_instance = intake_specialist.IntakeSpecialist(
                milestone_map,
                openai_api_key=openai_api_key,
                model=os.getenv(ENV_OPENAI_MODEL, DEFAULT_OPENAI_MODEL)
            )
            print(f"✓ Initialized Intake Specialist with OpenAI")
        else:
            print(f"⚠ Warning: {ENV_OPENAI_API_KEY} not set. Intake Specialist will not be available.")
            intake_specialist_instance = None
    except Exception as e:
        print(f"⚠ Warning: Could not initialize Intake Specialist: {e}")
        intake_specialist_instance = None
    
    # Load activities
    if ACTIVITIES_JSON.exists():
        with open(ACTIVITIES_JSON, 'r', encoding=DEFAULT_ENCODING) as f:
            activities_list = json.load(f)
        # Create a map for quick lookup by milestone_id
        activities_map = {
            activity["target_milestone_id"]: {
                "title": activity["title"],
                "materials": activity["materials"],
                "instructions": activity["instructions"],
                "benefit": activity["benefit"]
            }
            for activity in activities_list
        }
        print(f"✓ Loaded activities.json ({len(activities_map)} activities)")
    else:
        print(f"⚠ Warning: activities.json not found at {ACTIVITIES_JSON}")
        activities_map = {}
    
    print("✓ NextPlay API ready!")

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns basic information about the API, available endpoints, and
    the status of loaded data files.
    
    Returns:
        Dictionary containing API metadata and data status
    """
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": API_DESCRIPTION,
        "endpoints": {
            "POST /recommend": "Get personalized milestone recommendations with activities",
            "POST /intake": "Process parent's natural language description (Intake Specialist)",
            "GET /milestones": "List all available milestones",
            "GET /health": "Health check endpoint"
        },
        "status": "ready",
        "data_loaded": {
            "mastery_ages": len(mastery_ages),
            "transition_matrix": len(transition_matrix),
            "activities": len(activities_map)
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "data_loaded": {
            "mastery_ages": len(mastery_ages) > 0,
            "transition_matrix": len(transition_matrix) > 0,
            "activities": len(activities_map) > 0
        }
    }

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get personalized milestone recommendations with matching play activities.
    
    - **baby_age_months**: Baby's current age in months (must be >= 0)
    - **completed_milestone_ids**: List of milestone IDs the baby has already completed
    
    Returns up to 3 recommendations, each containing:
    - Milestone information (ID, name, scores, category, mastery age)
    - Matching play activity (title, materials, instructions, benefit)
    """
    try:
        # Use pre-loaded global data instead of reloading files
        csv_file = str(PROCESSED_CSV)
        
        # Prepare activities data for filtering
        # Create a set of milestone IDs that have activities
        available_milestone_ids = set(activities_map.keys())
        
        # Call the recommendation engine with pre-loaded data
        # Activities data is used to filter recommendations to only include milestones with activities
        recommendations = recommender.get_recommendations(
            user_completed_ids=request.completed_milestone_ids,
            baby_age_months=request.baby_age_months,
            csv_file=csv_file,
            transition_matrix_data=transition_matrix,
            mastery_ages_data=mastery_ages,
            milestone_map_data=milestone_map,
            activities_data=available_milestone_ids
        )
        
        # Enhance each recommendation with activity data
        enhanced_recommendations = []
        for rec in recommendations:
            milestone_id = rec.get("milestone_id")
            
            # Find matching activity
            activity = activities_map.get(milestone_id)
            
            if activity:
                # Combine milestone data with activity
                enhanced_rec = {
                    **rec,  # Include all milestone fields
                    "activity": activity
                }
            else:
                # If no activity found, create a generic one based on milestone name
                # This allows recommendations from full dataset when activities are exhausted
                milestone_name = rec.get("milestone_name", "Milestone")
                print(f"⚠ Warning: No activity found for milestone {milestone_id}. Using generic activity.")
                enhanced_rec = {
                    **rec,
                    "activity": {
                        "title": milestone_name,
                        "materials": ["household items"],
                        "instructions": [
                            f"Practice {milestone_name.lower()} with your baby in a safe, comfortable space.",
                            "Encourage and celebrate their efforts, and let them explore at their own pace."
                        ],
                        "benefit": f"Practicing {milestone_name.lower()} supports your baby's natural development journey."
                    }
                }
            
            enhanced_recommendations.append(enhanced_rec)
        
        return RecommendationResponse(recommendations=enhanced_recommendations)
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Required data file not found: {str(e)}. Please ensure all data files are generated."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Error in /recommend endpoint: {str(e)}")
        print(f"Traceback:\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/milestones")
async def list_milestones():
    """List all available milestones with their activities."""
    milestone_list = []
    
    for milestone_id, activity in activities_map.items():
        milestone_info = {
            "milestone_id": milestone_id,
            "activity_title": activity["title"]
        }
        
        # Try to get mastery age if available
        if milestone_id in mastery_ages:
            mastery_age = mastery_ages[milestone_id]
            if mastery_age is not None:
                milestone_info["mastery_age"] = mastery_age
        
        milestone_list.append(milestone_info)
    
    return {
        "total_milestones": len(milestone_list),
        "milestones": milestone_list
    }

class IntakeRequest(BaseModel):
    """Request model for intake endpoint."""
    description: str = Field(..., min_length=1, description="Parent's natural language description of their child")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "My baby Emma is 6 months old. She can sit without support and she's starting to crawl. She also smiles when we play with her."
            }
        }

class IntakeResponse(BaseModel):
    """Response model for intake endpoint."""
    child_name: Optional[str] = Field(None, description="Extracted child's name")
    age_months: Optional[float] = Field(None, ge=0, le=48, description="Child's age in months")
    completed_milestone_ids: List[str] = Field(default_factory=list, description="List of completed milestone IDs")
    needs_clarification: bool = Field(..., description="Whether clarification is needed")
    follow_up_question: Optional[str] = Field(None, description="Follow-up question if clarification is needed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "child_name": "Emma",
                "age_months": 6.0,
                "completed_milestone_ids": ["ddigmd063", "ddigmm066", "ddicmm030"],
                "needs_clarification": False,
                "follow_up_question": None
            }
        }

@app.post("/intake", response_model=IntakeResponse)
async def process_intake(request: IntakeRequest):
    """
    Process a parent's natural language description and extract structured developmental data.
    
    This endpoint acts as the NextPlay Intake Specialist, extracting:
    - Child's name (if mentioned)
    - Age in months
    - Completed milestones (mapped to GSED codes)
    
    Returns structured JSON with clarification questions if needed.
    """
    if intake_specialist_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Intake Specialist is not available. Please ensure milestone_map.json is loaded."
        )
    
    try:
        result = intake_specialist_instance.process_intake(request.description)
        return IntakeResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing intake: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

