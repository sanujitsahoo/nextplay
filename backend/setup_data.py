"""
Data setup script for NextPlay baby development recommender.
Loads and processes GCDG milestone data from RDA file.
"""

import pandas as pd
import pyreadr
import json
from pathlib import Path

# Import paths from config
from config import (
    TRAINING_DATA_DATA_DIR,
    TRAINING_DATA_MAN_DIR,
    RDA_FILE,
    DOC_FILE,
    MODELS_DIR,
    MILESTONE_MAP_JSON,
    PROCESSED_CSV
)

def extract_milestone_labels_from_doc(doc_file):
    """
    Extract milestone labels from the .Rd documentation file.
    Returns a dictionary mapping milestone codes to human-readable names.
    """
    milestone_map = {}
    
    if not doc_file.exists():
        print(f"Warning: Documentation file {doc_file} not found.")
        return milestone_map
    
    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the tabular format from .Rd file
    # Pattern: \code{ddiXXX} \tab 0/1 \tab Human readable label \cr
    import re
    # Match: \code{ddi...} followed by \tab 0/1 \tab and then the label until \cr or end of line
    # The label ends with optional \cr
    pattern = r'\\code\{(ddi[^}]+)\}\s*\\tab\s*0/1\s*\\tab\s*([^\\\r\n]+?)(?:\\cr)?\s*(?:\r|\n|$)'
    matches = re.findall(pattern, content)
    
    for code, label in matches:
        # Clean up the label (remove trailing/leading spaces)
        label = label.strip()
        milestone_map[code] = label
    
    return milestone_map

def infer_milestone_labels_from_code(milestone_codes):
    """
    Infer milestone labels using GSED 9-position schema.
    Domain identification:
    - 'c' = Cognitive (cg)
    - 'f' = Fine Motor (fm)
    - 'g' = Gross Motor (gm)
    """
    milestone_map = {}
    
    for code in milestone_codes:
        if not code.startswith('ddi'):
            continue
            
        # Extract the domain indicator (character after 'ddi')
        if len(code) > 4:
            domain_char = code[3]
            
            # Determine domain
            if domain_char == 'c':
                domain = "Cognitive"
            elif domain_char == 'f':
                domain = "Fine Motor"
            elif domain_char == 'g':
                domain = "Gross Motor"
            else:
                domain = "Unknown"
            
            # Create a readable label based on code
            milestone_map[code] = f"{domain} milestone {code}"
        else:
            milestone_map[code] = f"Milestone {code}"
    
    return milestone_map

def load_data():
    """Load data from RDA file using pyreadr."""
    print(f"Loading data from {RDA_FILE}...")
    
    if not RDA_FILE.exists():
        raise FileNotFoundError(f"Data file {RDA_FILE} not found.")
    
    # pyreadr.read_r returns a dictionary of DataFrames
    result = pyreadr.read_r(str(RDA_FILE))
    
    # The key is usually the object name without extension
    data_key = 'gcdg_nld_smocc'
    if data_key not in result:
        # Try to get the first (and likely only) key
        data_key = list(result.keys())[0]
    
    df = result[data_key]
    print(f"Loaded DataFrame with shape: {df.shape}")
    return df

def process_data(df):
    """
    Process the loaded data:
    1. Keep only subjid, agedays, sex, and columns starting with 'ddi'
    2. Convert agedays to age_months
    3. Fill missing values with -1 (untested), keep 1 (pass) and 0 (fail)
    """
    print("Processing data...")
    
    # Filter columns
    base_cols = ['subjid', 'agedays', 'sex']
    ddi_cols = [col for col in df.columns if col.startswith('ddi')]
    
    if not ddi_cols:
        raise ValueError("No columns starting with 'ddi' found in the data.")
    
    selected_cols = base_cols + ddi_cols
    df_processed = df[selected_cols].copy()
    
    print(f"Selected {len(selected_cols)} columns ({len(ddi_cols)} milestone columns)")
    
    # Convert agedays to age_months
    df_processed['age_months'] = df_processed['agedays'] / 30.44
    
    # Reorder columns: move age_months after agedays
    cols = ['subjid', 'agedays', 'age_months', 'sex'] + ddi_cols
    df_processed = df_processed[cols]
    
    # Process milestone columns: fill missing with -1, ensure 1 (pass) and 0 (fail)
    for col in ddi_cols:
        # Convert to numeric, coercing errors to NaN
        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
        # Fill NaN with -1 (untested)
        df_processed[col].fillna(-1, inplace=True)
        # Ensure values are 0, 1, or -1
        # Convert any other values (like 2, etc.) to -1 for safety
        df_processed[col] = df_processed[col].apply(
            lambda x: x if x in [0, 1, -1] else -1
        )
    
    print(f"Processed DataFrame shape: {df_processed.shape}")
    return df_processed, ddi_cols

def create_milestone_map(ddi_cols):
    """
    Create a mapping of milestone codes to human-readable names.
    First tries to extract from documentation, then falls back to inference.
    """
    print("Creating milestone mapping...")
    
    # Try to extract from documentation
    milestone_map = extract_milestone_labels_from_doc(DOC_FILE)
    
    # If documentation doesn't have all milestones, use inference as fallback
    missing_codes = [code for code in ddi_cols if code not in milestone_map]
    if missing_codes:
        print(f"  {len(missing_codes)} milestones not found in documentation, using inference...")
        inferred_map = infer_milestone_labels_from_code(missing_codes)
        milestone_map.update(inferred_map)
    
    print(f"Created mapping for {len(milestone_map)} milestones")
    return milestone_map

def get_top_milestones(df_processed, ddi_cols, n=20):
    """
    Get the top N most frequent milestones (by number of non-missing observations).
    """
    # Count non-missing (not -1) values for each milestone
    milestone_counts = {}
    for col in ddi_cols:
        count = (df_processed[col] != -1).sum()
        milestone_counts[col] = count
    
    # Sort by count and get top N
    sorted_milestones = sorted(milestone_counts.items(), key=lambda x: x[1], reverse=True)
    top_n = dict(sorted_milestones[:n])
    
    return top_n

def main():
    """Main function to orchestrate the data setup process."""
    print("=" * 60)
    print("NextPlay Data Setup")
    print("=" * 60)
    
    # Load data
    df = load_data()
    
    # Process data
    df_processed, ddi_cols = process_data(df)
    
    # Create milestone mapping
    milestone_map = create_milestone_map(ddi_cols)
    
    # Get top 20 most frequent milestones
    top_milestones = get_top_milestones(df_processed, ddi_cols, n=20)
    
    # Create mapping for top milestones only
    top_milestone_map = {code: milestone_map.get(code, f"Milestone {code}") 
                        for code in top_milestones.keys()}
    
    # Ensure models directory exists
    MODELS_DIR.mkdir(exist_ok=True)
    
    # Save processed data
    df_processed.to_csv(PROCESSED_CSV, index=False)
    print(f"\nSaved processed data to {PROCESSED_CSV}")
    
    # Save milestone mapping (top 20)
    with open(MILESTONE_MAP_JSON, 'w', encoding='utf-8') as f:
        json.dump(top_milestone_map, f, indent=2, ensure_ascii=False)
    print(f"Saved milestone mapping (top 20) to {MILESTONE_MAP_JSON}")
    
    print("\n" + "=" * 60)
    print("Data setup complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Total rows: {len(df_processed)}")
    print(f"  - Total milestones: {len(ddi_cols)}")
    print(f"  - Top 20 milestones mapped: {len(top_milestone_map)}")
    print(f"\nTop 5 most frequent milestones:")
    for i, (code, count) in enumerate(list(top_milestones.items())[:5], 1):
        label = milestone_map.get(code, "Unknown")
        print(f"  {i}. {code}: {label} ({count} observations)")

if __name__ == "__main__":
    main()

