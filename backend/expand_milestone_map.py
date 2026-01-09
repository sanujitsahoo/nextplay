"""
Script to expand milestone_map.json to include all milestones from the dataset.
"""

import pandas as pd
import json
from pathlib import Path
from config import MILESTONE_MAP_JSON, PROCESSED_CSV

# Manual mapping from the documentation file
MANUAL_MILESTONE_MAP = {
    "ddicmm029": "Reacts when spoken to",
    "ddicmm030": "Smiles in response (M; can ask parents)",
    "ddicmm031": "Vocalizes in response",
    "ddicmm033": "Says dada, baba, gaga",
    "ddicmm034": "Babbles while playing",
    "ddicmm036": "Waves 'bye-bye' (M; can ask parents)",
    "ddicmm037": "Uses two words with comprehension",
    "ddicmm039": "Says three 'words'",
    "ddicmm041": "Says sentences with 2 words",
    "ddicmm043": "Refers to self using 'me' or 'I' (M; can ask parents)",
    "ddicmd044": "Points at 5 pictures in the book",
    "ddicmd116": "Turn head to sound",
    "ddicmd136": "Reacts to verbal request (M; can ask parents)",
    "ddicmd141": "Identifies two named objects",
    "ddicmd148": "Understands 'play' orders",
    "ddifmd001": "Eyes fixate",
    "ddifmd002": "Follows with eyes and head 30d  < 0 > 30d",
    "ddifmd003": "Hands open occasionally",
    "ddifmm004": "Watches own hands",
    "ddifmd005": "Plays with hands in midline",
    "ddifmd007": "Passes cube from hand to hand",
    "ddifmd008": "Holds cube, grasps another one with other hand",
    "ddifmm009": "Plays with both feet",
    "ddifmd010": "Picks up pellet between thumb and index finger",
    "ddifmd011": "Puts cube in and out of a box",
    "ddifmm012": "Plays 'give and take' (M; can ask parents)",
    "ddifmd013": "Tower of 2 cubes",
    "ddifmm014": "Explores environment energetically (M; can ask parents)",
    "ddifmd015": "Builds tower of 3 cubes",
    "ddifmm016": "Imitates everyday activities (M; can ask parents)",
    "ddifmd017": "Tower of 6 cubes",
    "ddifmd018": "Places round block in board",
    "ddifmm019": "Takes off shoes and socks (M; can ask parents)",
    "ddifmd154": "Eats with spoon without help (M; can ask parents)",
    "ddigmd006": "Grasps object within reach",
    "ddigmd052": "Moves arms equally well",
    "ddigmd053": "Moves legs equally well",
    "ddigmd054": "Stays suspended when lifted under the armpits",
    "ddigmd055": "No head lag if pulled to sitting",
    "ddigmd056": "Lifts chin off table for a moment",
    "ddigmd057": "Lifts head to 45 degrees on prone position",
    "ddigmd058": "Looks around to side with angle face-table 90",
    "ddigmd059": "Flexes or stomps legs while being swung",
    "ddigmm060": "Rolls over back to front",
    "ddigmd061": "Balances head well while sitting",
    "ddigmd062": "Sits on buttocks while legs stretched",
    "ddigmd063": "Sits in stable position without support",
    "ddigmm064": "Crawls forward, abdomen on the floor",
    "ddigmm065": "Pulls up to standing position",
    "ddigmm066": "Crawls, abdomen off the floor (M; can ask parents)",
    "ddigmm067": "Walks while holding onto play-pen or furniture",
    "ddigmd068": "Walks alone",
    "ddigmd069": "Throws ball without falling",
    "ddigmd070": "Squats or bends to pick things up",
    "ddigmd071": "Kicks ball",
    "ddigmd146": "Drinks from cup (M; can ask parents)",
    "ddigmd168": "Walks well"
}

def main():
    # Load existing milestone_map
    with open(MILESTONE_MAP_JSON, 'r') as f:
        milestone_map = json.load(f)
    
    print(f'Current entries: {len(milestone_map)}')
    
    # Get all milestone columns from processed CSV
    df = pd.read_csv(PROCESSED_CSV)
    milestone_cols = [col for col in df.columns if col.startswith('ddi')]
    print(f'Total milestones in dataset: {len(milestone_cols)}')
    
    # Update milestone_map with all milestones from dataset
    added_count = 0
    for milestone_id in milestone_cols:
        if milestone_id not in milestone_map:
            if milestone_id in MANUAL_MILESTONE_MAP:
                milestone_map[milestone_id] = MANUAL_MILESTONE_MAP[milestone_id]
            else:
                # Use inferred name
                if len(milestone_id) > 3:
                    domain_char = milestone_id[3].lower()
                    if domain_char == 'c':
                        domain = 'Cognitive'
                    elif domain_char == 'f':
                        domain = 'Fine Motor'
                    elif domain_char == 'g':
                        domain = 'Gross Motor'
                    else:
                        domain = 'Unknown'
                    milestone_map[milestone_id] = f'{domain} milestone {milestone_id}'
                else:
                    milestone_map[milestone_id] = f'Milestone {milestone_id}'
            added_count += 1
    
    # Save expanded milestone_map
    with open(MILESTONE_MAP_JSON, 'w', encoding='utf-8') as f:
        json.dump(milestone_map, f, indent=2, ensure_ascii=False)
    
    print(f'\n✓ Expanded {MILESTONE_MAP_JSON.name} to {len(milestone_map)} entries')
    print(f'  (Added {added_count} new milestones)')
    
    # Verify
    missing = [m for m in milestone_cols if m not in milestone_map]
    if missing:
        print(f'\n⚠ Warning: {len(missing)} milestones still missing from map')
    else:
        print(f'\n✓ All {len(milestone_cols)} milestones are now in the map!')

if __name__ == '__main__':
    main()

