import os
import sqlite3
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

TMDB_KEY = os.getenv("TMDB_API_KEY")
IMDB_LIST_ID = os.getenv("IMDB_LIST_ID", "ur146714887")
DB_PATH = "movies.db"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------
# DATABASE INITIALIZATION (FIXED: cast_list instead of cast)
# -------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            tmdb_id INTEGER PRIMARY KEY,
            title TEXT,
            genres TEXT,
            overview TEXT,
            cast_list TEXT,
            directors TEXT,
            keywords TEXT,
            popularity REAL,
            poster TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------
def fetch_imdb_watchlist():
    url = f"https://www.imdb.com/user/{IMDB_LIST_ID}/watchlist"
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers).text

    import re
    ids = list(set(re.findall(r"tt\\d+", html)))
    return ids


def imdb_to_tmdb(imdb_id):
    url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={TMDB_KEY}&external_source=imdb_id"
    r = requests.get(url).json()
    results = r.get("movie_results") or r.get("tv_results") or []
    if not results:
        return None
    return results[0]["id"]


def fetch_tmdb_movie(tmdb_id):
    url = (
        f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        f"?api_key={TMDB_KEY}&append_to_response=credits,keywords"
    )
    return requests.get(url).json()


def store_movie(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO movies
        (tmdb_id, title, genres, overview, cast_list, directors, keywords, popularity, poster)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["tmdb_id"],
            data["title"],
            ",".join(data["genres"]),
            data["overview"],
            ",".join(data["cast"]),
            ",".join(data["directors"]),
            ",".join(data["keywords"]),
            data["popularity"],
            data["poster"],
        ),
    )
    conn.commit()
    conn.close()

# -------------------------------------------------------
# SYNC ENDPOINT (GET + POST)
# -------------------------------------------------------
@app.api_route("/sync", methods=["GET", "POST"])
def sync_watchlist():
    imdb_ids = fetch_imdb_watchlist()
    tmdb_ids = []

    for imdb_id in imdb_ids:
        tmdb_id = imdb_to_tmdb(imdb_id)
        if tmdb_id:
            tmdb_ids.append(tmdb_id)

    for tmdb_id in tmdb_ids:
        data = fetch_tmdb_movie(tmdb_id)
        if "id" not in data:
            continue

        movie_data = {
            "tmdb_id": data["id"],
            "title": data.get("title") or data.get("name"),
            "genres": [g["name"] for g in data.get("genres", [])],
            "overview": data.get("overview", ""),
            "cast": [c["name"] for c in data.get("credits", {}).get("cast", [])[:5]],
            "directors": [
                c["name"]
                for c in data.get("credits", {}).get("crew", [])
                if c.get("job") == "Director"
            ],
            "keywords": [
                k["name"]
                for k in data.get("keywords", {}).get("keywords", [])
            ],
            "popularity": data.get("popularity", 0),
            "poster": data.get("poster_path"),
        }

        store_movie(movie_data)

    return {"status": "ok", "synced": len(tmdb_ids)}

# -------------------------------------------------------
# RECOMMENDATIONS (FIXED: cast_list selected properly)
# -------------------------------------------------------
@app.get("/recommendations")
def recommendations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT tmdb_id, title, genres, overview, cast_list, directors, keywords, popularity, poster FROM movies"
    )
    rows = c.fetchall()
    conn.close()

    import random

    recs = {
        "Because You Watched…": random.sample(rows, min(10, len(rows))),
        "Dark / Psychological": random.sample(rows, min(10, len(rows))),
        "Slow-Burn Character Films": random.sample(rows, min(10, len(rows))),
        "High Popularity Picks": sorted(rows, key=lambda x: -x[7])[:10],
    }
    return recs

@app.get("/health")
def health():
    return {"status": "ok"}
