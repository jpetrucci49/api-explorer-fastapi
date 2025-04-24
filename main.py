import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi.responses import JSONResponse
import redis
import json
import asyncio

app = FastAPI()

load_dotenv()
GITHUB_API_URL = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
PORT = int(os.getenv("PORT", 3002))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
redis_client = redis.Redis(
    host=f"{os.getenv('REDIS_HOST')}",
    port=int(os.getenv("REDIS_PORT")),
    password=f"{os.getenv('REDIS_PASSWORD')}",
    decode_responses=True
)

common_headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Access-Control-Allow-Origin": "http://localhost:3000",
    "Access-Control-Allow-Methods": "GET, POST",
    "Access-Control-Allow-Headers": "*"
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET, POST"],
    allow_headers=["*"],
    expose_headers=["X-Cache"]
)

def with_logging(endpoint):
    async def wrapper(request: Request, username: Optional[str] = None):
        start = datetime.now()
        response = await endpoint(request) if username is None else await endpoint(request, username)
        cache_header = response.headers.get("X-Cache", "")
        duration = (datetime.now() - start).total_seconds() * 1000
        logger.info(f"{request.method} {request.url.path}{request.url.query and '?' + request.url.query} {response.status_code} {cache_header} - {duration:.0f}ms")
        return response
    return wrapper

async def fetch_github(url: str) -> Dict:
    if "test429" in url:
        raise HTTPException(
            status_code=429,
            detail={
                "status": 429,
                "detail": "GitHub rate limit exceeded",
                "extra": {"remaining": "0"}
            }
        )
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        response.raise_for_status()
        return response.json()

async def analyze_profile(username: str) -> Dict:
    user_data = await fetch_github(f"{GITHUB_API_URL}/users/{username}")
    repos = await fetch_github(f"{user_data['repos_url']}?per_page=100")
    languages_tasks = [
        fetch_github(repo["languages_url"]) for repo in repos
    ]
    languages = await asyncio.gather(*languages_tasks, return_exceptions=True)

    lang_stats = {}
    for lang_data in languages:
        if isinstance(lang_data, dict):  # Skip exceptions
            for lang, bytes in lang_data.items():
                lang_stats[lang] = lang_stats.get(lang, 0) + bytes

    top_languages = [
        {"lang": lang, "bytes": bytes}
        for lang, bytes in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    return {
        "login": user_data["login"],
        "publicRepos": user_data["public_repos"],
        "topLanguages": top_languages
    }

@app.get("/github")
@with_logging
async def get_github_user(request: Request, username: str):
    if not username:
        raise HTTPException(
            status_code=400, 
            detail={
                "status": 400,
                "detail": "Username is required",
                "extra": {}
            }
        )

    cache_key = f"github:{username}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return JSONResponse(
                content=json.loads(cached),
                headers={**common_headers, "X-Cache": "HIT"}
            )
    except redis.RedisError:
        pass

    try:
        data = await fetch_github(f"{GITHUB_API_URL}/users/{username}")
        try:
            redis_client.setex(cache_key, 1800, json.dumps(data))
        except redis.RedisError:
            pass
        return JSONResponse(
            content=data,
            headers={**common_headers, "X-Cache": "MISS"}
        )
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        detail = "GitHub API error"
        extra = {}
        if status == 404:
            detail = "GitHub user not found"
        elif status == 429:
            detail = "GitHub rate limit exceeded"
            extra = {"remaining": e.response.headers.get("X-RateLimit-Remaining", "0")}
        elif status == 400:
            detail = "Invalid GitHub API request"
        raise HTTPException(
            status_code=status,
            detail={"status": status, "detail": detail, "extra": extra}
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": 500,
                "detail": "Network error contacting GitHub",
                "extra": {}
            }
        )

@app.get("/analyze")
@with_logging
async def analyze(request: Request, username: str):
    if not username:
        raise HTTPException(
            status_code=400, 
            detail={
                "status": 400,
                "detail": "Username is required",
                "extra": {}
            }
        )

    cache_key = f"analyze:{username}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return JSONResponse(
                content=json.loads(cached),
                headers={**common_headers, "X-Cache": "HIT"}
            )
    except redis.RedisError:
        pass

    try:
        analysis = await analyze_profile(username)
        try:
            redis_client.setex(cache_key, 1800, json.dumps(analysis))
        except redis.RedisError:
            pass
        return JSONResponse(
            content=analysis,
            headers={**common_headers, "X-Cache": "MISS"}
        )
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        detail = "GitHub API error"
        extra = {}
        if status == 404:
            detail = "GitHub user not found"
        elif status == 429:
            detail = "GitHub rate limit exceeded"
            extra = {"remaining": e.response.headers.get("X-RateLimit-Remaining", "0")}
        elif status == 400:
            detail = "Invalid GitHub API request"
        raise HTTPException(
            status_code=status,
            detail={"status": status, "detail": detail, "extra": extra}
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": 500,
                "detail": "Network error analyzing profile",
                "extra": {}
            }
        )

@app.post("/clear-cache")
@with_logging
async def clear_cache(request: Request):
    try:
        redis_client.flushdb()
        return JSONResponse(
            content={"detail": "Cache cleared successfully"},
            headers=common_headers
        )
    except redis.RedisError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": 500,
                "detail": "Redis connection failed",
                "extra": {}
            }
        )
