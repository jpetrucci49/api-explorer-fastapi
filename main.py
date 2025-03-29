import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from datetime import datetime
from typing import Dict
from fastapi.responses import JSONResponse

app = FastAPI()

load_dotenv()
GITHUB_API_URL = "https://api.github.com/users"
TOKEN = os.getenv("GITHUB_TOKEN")
PORT = int(os.getenv("PORT", 3002))
CACHE_TTL = 30 * 60

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
cache: Dict[str, Dict[str, any]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

def with_logging(endpoint):
    async def wrapper(request: Request, username: str):
        start = datetime.now()
        response = await endpoint(request, username)
        cache_header = response.headers.get("X-Cache", "")
        duration = (datetime.now() - start).total_seconds() * 1000
        logger.info(f"{request.method} {request.url.path}{request.url.query and '?' + request.url.query} {response.status_code} {cache_header} - {duration:.0f}ms")
        return response
    return wrapper

@app.get("/github")
@with_logging
async def get_github_user(request: Request, username: str):
    cache_key = f"github:{username}"
    cached = cache.get(cache_key)
    if cached and (datetime.now() - cached["timestamp"]).total_seconds() < CACHE_TTL:
        return JSONResponse(
            content=cached["data"],
            headers={
                "X-Cache": "HIT",
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )

    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {TOKEN}"}
            response = await client.get(f"{GITHUB_API_URL}/{username}", headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="GitHub API error")
            data = response.json()
            cache[cache_key] = {"data": data, "timestamp": datetime.now()}
            return JSONResponse(
                content=data,
                headers={
                    "X-Cache": "MISS",
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Failed to reach GitHub")
