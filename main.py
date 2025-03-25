from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

GITHUB_API_URL = "https://api.github.com/users"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/github")
async def get_github_user(username: str):
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{GITHUB_API_URL}/{username}")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="GitHub API error")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Failed to reach GitHub")