# Vexora Intelligence 2.0

## What this is
Vexora Intelligence is an end-to-end, edge-deployable computer vision platform that transforms passive CCTV feeds into a live, interactive 3D digital twin of a retail store. Built for the Purplle Tech Challenge, it tracks unique visitors, calculates true conversion rates, generates heatmaps, and filters out staff using Gemini AI.

## Tech Stack
- **Detection & Tracking**: YOLOv8 + ByteTrack (person tracking across cameras)
- **Staff Filtering**: Google Gemini Vision API + HSV Color Masking
- **Backend Edge Data Layer**: FastAPI + SQLite (WAL mode)
- **Live 3D Dashboard**: Next.js, React Three Fiber, TailwindCSS, Server-Sent Events (SSE)
- **Containerized**: Docker Compose

## Quick Start (Run Locally)

The web infrastructure is fully containerized for a seamless setup. 

### Step 1: Boot the Web Infrastructure (Docker)
```bash
git clone https://github.com/xyushman/Vexora-Store-intelligence.git
cd Vexora-Store-intelligence
docker compose up --build -d
```
- **Dashboard UI**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **API Docs (Swagger)**: `http://localhost:8000/docs`

### Step 2: Upload POS Data
To calculate true conversion rates, upload the cash-register receipts:
```bash
curl -X POST http://localhost:8000/pos/upload \
  -F "file=@Brigade_Bangalore_10_April_26 (1)bc6219c.csv" \
  -H "X-API-Key: purplle-tech-challenge-2024"
```

### Step 3: Run the AI Computer Vision Pipeline
We decoupled the heavy YOLOv8 processing from the web container to ensure the API never crashes. Open a new terminal and run:

```powershell
# Create environment
python -m venv venv
.\venv\Scripts\activate
pip install -r pipeline/requirements.txt
pip install ultralytics torch torchvision shapely opencv-python pydantic

# Execute the pipeline orchestrator
powershell -ExecutionPolicy Bypass -File pipeline/run.ps1 -ClipsDir "CCTV Footage" -StoreId "ST1008"
```
The script will analyze all cameras, filter false positives/posters using custom spatial heuristics, and stream live telemetry events directly to the FastAPI backend.

### Step 4: View the Digital Twin
Open your browser to `http://localhost:3000`. As the PowerShell script processes the video, the 3D Store Heatmap will light up, glowing agents will wander the store, and the Conversion Funnel will dynamically update in real-time.
