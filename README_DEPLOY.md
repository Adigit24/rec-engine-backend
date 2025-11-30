# Rec Engine Backend (Render Deployment)

## 1. Upload these files to a GitHub repo:
- rec_backend_main.py
- requirements.txt
- Dockerfile
- render.yaml

## 2. Go to Render.com → New Web Service
- Connect your GitHub
- Pick the repo
- Render auto-detects Dockerfile

## 3. Add Environment Variables:
- TMDB_API_KEY = your TMDB key
- IMDB_LIST_ID = ur146714887
- SYNC_ON_START = true (optional)

## 4. Deploy

## 5. After deploy:
https://yourapp.onrender.com/health
https://yourapp.onrender.com/sync
https://yourapp.onrender.com/recommendations
