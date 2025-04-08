# API Explorer FastAPI Backend

A RESTful API built with Python and FastAPI to fetch and cache GitHub user data. Integrates with the [API Explorer Frontend](https://github.com/jpetrucci49/api-explorer-frontend).

## Features

- Endpoint: `/github?username={username}`
- Returns GitHub user details (e.g., login, id, name, repos, followers).
- Redis caching with 30-minute TTL.

## Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/jpetrucci49/api-explorer-fastapi.git
   cd api-explorer-fastapi
   ```
2. **Install dependencies**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run locally**  
   ```bash
   make dev
   ```
   Runs on `http://localhost:3002`. Requires Redis at `redis:6379`.  
   *Note*: If `make` isn’t installed:  
   ```bash
   source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 3002 --reload
   ```

## Usage

- GET `/github?username=octocat` to fetch data for "octocat".
- Test with `curl -v` (check `X-Cache`) or the frontend.

## Example Response

```json
{
  "login": "octocat",
  "id": 583231,
  "name": "The Octocat",
  "public_repos": 8,
  "followers": 17529
}
```

## Next Steps

- Add `/analyze` endpoint for profile insights (e.g., language stats).
- Add `/network` endpoint for collaboration mapping.
- Deploy to Render or Fly.io.

---
Built by Joseph Petrucci | March 2025