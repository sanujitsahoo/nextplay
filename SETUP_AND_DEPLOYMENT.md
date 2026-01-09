# NextPlay Setup and Deployment Guide

This guide covers both local development setup and production deployment for the NextPlay application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Data Files Generation](#data-files-generation)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **npm** or **yarn** (comes with Node.js)
- **pip** (Python package manager)

### Required Files for Production

Ensure these files exist in `backend/models/` directory (see [Data Files Generation](#data-files-generation)):

- `processed_milestones.csv` - Processed milestone data
- `mastery_ages.json` - Calculated mastery ages
- `transition_matrix.json` - Transition probability matrix
- `milestone_map.json` - Human-readable milestone names
- `activities.json` - Play activities for milestones

---

## Local Development Setup

This section covers setting up NextPlay for local development and testing.

### Backend Setup

#### Step 1: Navigate to backend directory
```bash
cd backend
```

#### Step 2: Create and activate virtual environment
```bash
# Create virtual environment in parent directory
python3 -m venv ../nexplay_env

# Activate virtual environment
# On macOS/Linux:
source ../nexplay_env/bin/activate

# On Windows:
# ..\nexplay_env\Scripts\activate
```

#### Step 3: Install Python dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Generate data files (first time only)
```bash
# Process raw data
python setup_data.py

# Generate mastery ages and transition matrix
python engine_logic.py
```

**Note:** These scripts require the `training_data/` folder with raw `.rda` files. If you're cloning the repository without training data, you'll need to obtain these files separately or use pre-generated model files.

#### Step 5: Set up environment variables (optional)
Create a `.env` file in the `backend/` directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```

#### Step 6: Start the FastAPI server
```bash
# Option 1: Using uvicorn directly (recommended for development)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Python (if main.py has server code)
python main.py
```

✅ Backend will be running at: **http://localhost:8000**  
📚 API documentation: **http://localhost:8000/docs**

---

### Frontend Setup

#### Step 1: Open a NEW terminal window/tab

#### Step 2: Navigate to frontend directory
```bash
cd frontend
```

#### Step 3: Install Node.js dependencies (first time only)
```bash
npm install
```

#### Step 4: Start the Next.js development server
```bash
npm run dev
```

✅ Frontend will be running at: **http://localhost:3000**

---

### Quick Commands Reference (Local Development)

#### Backend (Terminal 1)
```bash
cd backend
source ../nexplay_env/bin/activate  # macOS/Linux
# OR
..\nexplay_env\Scripts\activate  # Windows

# First time only:
pip install -r requirements.txt
python setup_data.py
python engine_logic.py

# Start server:
uvicorn main:app --reload --port 8000
```

#### Frontend (Terminal 2)
```bash
cd frontend
npm install  # First time only
npm run dev
```

---

### Verify Local Setup

1. **Backend**: Visit http://localhost:8000/docs - you should see the FastAPI documentation
2. **Frontend**: Visit http://localhost:3000 - you should see the NextPlay landing page
3. **Health Check**: Visit http://localhost:8000/health - should return `{"status": "healthy"}`

---

## Production Deployment

This section covers deploying NextPlay to production environments.

### Backend Deployment

#### Option 1: Render.com (Recommended)

1. **Create a new Web Service** on Render.com

2. **Connect your repository** or upload files

3. **Configure Build & Start Commands:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables:**
   - `OPENAI_API_KEY` - Your OpenAI API key (for Intake Specialist)
   - `OPENAI_MODEL` - (Optional) OpenAI model to use (default: `gpt-4o-mini`)

5. **Upload Data Files:**
   - Upload all JSON and CSV files from `backend/models/` directory
   - Ensure files are in the same directory structure as your local setup

6. **Deploy:**
   - Render will automatically deploy on git push
   - Monitor logs for startup messages confirming data files are loaded

#### Option 2: Railway

1. **Create a new project** on Railway

2. **Connect your repository** or upload files

3. **Configure:**
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** 3.9+

4. **Set Environment Variables:**
   - Add `OPENAI_API_KEY` and optional `OPENAI_MODEL`

5. **Add Data Files:**
   - Upload JSON and CSV files from `backend/models/` to the project

#### Option 3: Docker

1. **Create Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Copy model files (ensure they exist in backend/models/)
COPY backend/models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Build and Run:**
```bash
docker build -t nextplay-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key nextplay-backend
```

#### Option 4: AWS/GCP/Azure

Follow standard Python web application deployment procedures:

1. **Set up a virtual environment**
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Upload model files** to the server
4. **Set environment variables** (OPENAI_API_KEY, etc.)
5. **Run with production server:**
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

**Important:** Ensure all files in `backend/models/` are present on the server.

---

### Frontend Deployment

#### Option 1: Vercel (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   cd frontend
   vercel
   ```

3. **Configure Environment Variables:**
   - In Vercel dashboard, set `NEXT_PUBLIC_API_URL` to your backend URL (e.g., `https://your-backend.onrender.com`)

4. **Update CORS Settings:**
   - In `backend/config.py`, ensure your Vercel URL is included in `ALLOWED_ORIGINS` or matches the `VERCEL_ORIGIN_REGEX` pattern

#### Option 2: Netlify

1. **Connect your repository** to Netlify

2. **Configure Build Settings:**
   - **Build command:** `cd frontend && npm run build`
   - **Publish directory:** `frontend/.next` (or `frontend/out` if using static export)

3. **Set Environment Variables:**
   - `NEXT_PUBLIC_API_URL` - Your backend API URL

#### Option 3: Self-Hosted

1. **Build the application:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Start the production server:**
   ```bash
   npm start
   ```

3. **Use a reverse proxy** (nginx, Apache) to serve the application

---

## Data Files Generation

### Overview

The NextPlay backend requires pre-generated model files to function. These files are created during the "training phase" and then used in production.

### Required Files

All files should be in the `backend/models/` directory:

1. **processed_milestones.csv** - Processed clinical milestone data
2. **mastery_ages.json** - Calculated mastery ages for each milestone
3. **transition_matrix.json** - Probabilistic transition matrix
4. **milestone_map.json** - Human-readable milestone names
5. **activities.json** - Play activities mapped to milestones (manually created)

### Generation Steps

**Prerequisites:** You need the `training_data/` folder with:
- `training_data/data/gcdg_nld_smocc.rda` - Raw milestone data
- `training_data/man/` - Documentation files for milestone labels

**Generate files:**
```bash
cd backend

# Step 1: Process raw data
python setup_data.py
# Creates: models/processed_milestones.csv, models/milestone_map.json

# Step 2: Calculate mastery ages and transition matrix
python engine_logic.py
# Creates: models/mastery_ages.json, models/transition_matrix.json

# Step 3: Manually create or update activities.json
# This file maps milestones to play activities (title, materials, instructions, benefit)
```

### File Sizes (Typical)

- `processed_milestones.csv`: ~5-10 MB
- `mastery_ages.json`: ~50-100 KB
- `transition_matrix.json`: ~100-200 KB
- `milestone_map.json`: ~20-50 KB
- `activities.json`: ~50-100 KB

**Note:** For production deployment, you only need the files in `models/`. The `training_data/` folder is not required in production and is excluded from git.

---

## Environment Variables

### Backend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes (for Intake) | - | OpenAI API key for natural language processing |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |

**Setup:**
- **Local:** Create `backend/.env` file (excluded from git)
- **Production:** Set in your hosting platform's environment variable settings

### Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API URL |

**Setup:**
- **Local:** Uses default `http://localhost:8000`
- **Production:** Set in your hosting platform's environment variable settings (e.g., Vercel, Netlify)

---

## Troubleshooting

### Local Development Issues

#### Backend

**Issue**: `FileNotFoundError: mastery_ages.json not found`
- **Solution**: Run `python setup_data.py` and `python engine_logic.py` first

**Issue**: `ModuleNotFoundError: No module named 'fastapi'`
- **Solution**: Make sure virtual environment is activated and run `pip install -r requirements.txt`

**Issue**: Port 8000 already in use
- **Solution**: Change port: `uvicorn main:app --reload --port 8001`

**Issue**: `ValueError: numpy.dtype size changed`
- **Solution**: Update pandas and numpy versions: `pip install pandas>=1.3.0,<2.0.0 numpy>=1.20.0,<1.25.0`

#### Frontend

**Issue**: `Error: API error: Failed to fetch`
- **Solution**: Make sure backend is running on http://localhost:8000

**Issue**: `Module not found` errors
- **Solution**: Run `npm install` in the frontend directory

**Issue**: Port 3000 already in use
- **Solution**: Next.js will automatically use port 3001

### Production Deployment Issues

#### Backend

**"Data file not found" errors**
- **Solution:** Ensure all JSON and CSV files from `backend/models/` are uploaded to your server in the correct directory structure

**"Intake Specialist not available"**
- **Solution:** Set the `OPENAI_API_KEY` environment variable. The Intake Specialist is optional - recommendations will still work without it.

**CORS errors**
- **Solution:** Update `ALLOWED_ORIGINS` in `backend/config.py` to include your frontend URL, or ensure your frontend URL matches the `VERCEL_ORIGIN_REGEX` pattern

**Port binding errors**
- **Solution:** Use the `$PORT` environment variable provided by your hosting platform, or set a specific port in your start command

#### Frontend

**"Failed to fetch" errors**
- **Solution:**
  1. Check that `NEXT_PUBLIC_API_URL` is set correctly in your hosting platform
  2. Verify backend is running and accessible
  3. Check CORS configuration in backend

**Build errors**
- **Solution:**
  1. Ensure Node.js version is 18+
  2. Delete `node_modules` and `package-lock.json`, then reinstall:
     ```bash
     rm -rf node_modules package-lock.json
     npm install
     ```

### Performance Issues

#### Slow API responses
- **Solution:**
  1. Ensure data files are pre-loaded (check startup logs)
  2. Use a production ASGI server (gunicorn with uvicorn workers)
  3. Enable caching if using a reverse proxy

#### Large bundle size
- **Solution:**
  1. Run `npm run build` to analyze bundle size
  2. Consider code splitting for large components
  3. Optimize images and assets

---

## Health Checks

### Backend Health Check

```bash
curl https://your-backend-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "data_loaded": {
    "mastery_ages": true,
    "transition_matrix": true,
    "activities": true
  }
}
```

### API Documentation

Visit `https://your-backend-url.com/docs` for interactive API documentation.

---

## Monitoring

### Backend Logs

Monitor startup logs for:
- ✓ Data files loaded successfully
- ✓ Intake Specialist initialized (if API key provided)
- ✓ API ready message

### Frontend Logs

Monitor for:
- API connection errors
- Failed recommendation fetches
- localStorage errors

---

## Security Considerations

1. **API Keys:** Never commit API keys to version control. Use environment variables and ensure `.env` is in `.gitignore`.

2. **CORS:** Restrict CORS origins in production to your specific frontend domain(s). Update `backend/config.py` accordingly.

3. **Rate Limiting:** Consider implementing rate limiting for production use to prevent abuse.

4. **HTTPS:** Always use HTTPS in production. Most hosting platforms (Render, Vercel, etc.) provide this automatically.

5. **Data Privacy:** Ensure compliance with data privacy regulations (GDPR, COPPA, etc.) if handling user data.

---

## Scaling

### Backend Scaling

- Use a load balancer for multiple backend instances
- Consider caching recommendations for common age/completion combinations
- Use a database for user progress tracking (future enhancement)
- Monitor memory usage (pre-loaded data files stay in memory)

### Frontend Scaling

- Use CDN for static assets (automatic with Vercel/Netlify)
- Enable Next.js image optimization
- Consider server-side rendering for better performance
- Monitor bundle size and optimize accordingly

---

## Stopping Servers (Local Development)

- **Backend**: Press `Ctrl+C` in the backend terminal
- **Frontend**: Press `Ctrl+C` in the frontend terminal
- **Virtual Environment**: Run `deactivate` to exit the virtual environment

---

## Support

For issues or questions:
1. Check the logs for error messages
2. Review the technical documentation (`TECHNICAL_DOCUMENTATION.html`)
3. Review the system architecture (`SYSTEM_ARCHITECTURE.html`)
4. Verify all prerequisites are met
5. Check that data files are correctly generated and present

