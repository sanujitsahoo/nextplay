# NextPlay - Baby Development Recommender

A full-stack application that provides personalized baby development milestone recommendations with play activities, powered by clinical milestone data and machine learning.

## Project Structure

```
nextplay/
├── backend/              # Python FastAPI backend
│   ├── models/          # Generated model files (JSON/CSV) - used in production
│   ├── training_data/   # Raw training data (.rda, .Rd) - excluded from git
│   ├── tests/           # Test suite
│   ├── docs/            # Backend documentation
│   ├── setup_data.py    # Data preprocessing script (training)
│   ├── engine_logic.py  # Data processing (mastery ages, transition matrix)
│   ├── recommender.py   # Recommendation engine logic
│   ├── main.py          # FastAPI application
│   └── requirements.txt # Python dependencies
│
├── frontend/            # Next.js 15 frontend
│   ├── app/             # Next.js app directory
│   ├── components/      # React components
│   └── package.json     # Node.js dependencies
│
├── TECHNICAL_DOCUMENTATION.html  # Technical deep dive
├── SYSTEM_ARCHITECTURE.html      # System architecture overview
└── nexplay_env/         # Python virtual environment (optional, excluded from git)
```

## Quick Start

> **📖 For detailed setup and deployment instructions, see [SETUP_AND_DEPLOYMENT.md](./SETUP_AND_DEPLOYMENT.md)**

### Backend Setup (Terminal 1)

```bash
cd backend

# Create and activate virtual environment
python3 -m venv ../nexplay_env
source ../nexplay_env/bin/activate  # macOS/Linux
# On Windows: ..\nexplay_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate data files (first time only)
python setup_data.py
python engine_logic.py

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

✅ Backend running at: **http://localhost:8000**  
📚 API Docs: **http://localhost:8000/docs**

### Frontend Setup (Terminal 2)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

✅ Frontend running at: **http://localhost:3000**

## Features

### Backend
- **Data Processing**: Loads and processes milestone data from RDA files
- **Recommendation Engine**: Calculates mastery ages and transition probabilities
- **REST API**: FastAPI endpoints for recommendations
- **Activity Mapping**: Maps milestones to play activities

### Frontend
- **Responsive Dashboard**: Mobile-friendly UI with pastel color scheme
- **Personalized Recommendations**: Age-appropriate milestone suggestions
- **Play Activities**: Interactive cards with materials, instructions, and benefits
- **Progress Tracking**: Save completed milestones locally

## API Endpoints

- `POST /recommend` - Get personalized recommendations
- `GET /health` - Health check
- `GET /milestones` - List all milestones

See `backend/README.md` and `backend/docs/README_API.md` for detailed API documentation.

## Development

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

See `backend/tests/README.md` for detailed testing documentation.

### Generating Model Files (Training Phase)

The backend requires model files in `backend/models/` to be generated during the training phase:

```bash
cd backend

# Process raw training data
python setup_data.py      # Creates processed_milestones.csv and milestone_map.json

# Generate models
python engine_logic.py    # Creates mastery_ages.json and transition_matrix.json
```

**Note**: The `training_data/` folder is only needed during this training phase. For production deployment, only the generated files in `models/` are required (and the `training_data/` folder is excluded from git).

## Technologies

### Backend
- Python 3.9+
- FastAPI
- Pandas
- NumPy
- pyreadr

### Frontend
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS

## License

