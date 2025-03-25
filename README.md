# API Explorer FastAPI Backend

A RESTful API built with Python and FastAPI to fetch GitHub user data. Integrates with the [API Explorer Frontend](https://github.com/jpetrucci49/api-explorer-frontend).

## Features
- Endpoint: `/github?username={username}`
- Returns GitHub user details (e.g., login, id, name, repos, followers)

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
   Runs on `http://localhost:3002`. Activates the venv automatically.  
   *Note*: If `make` isn’t installed (e.g., some Windows users), use:  
   ```bash
   source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 3002 --reload
   ```

## Usage
- GET `/github?username=octocat` to fetch data for "octocat"
- Test with `curl` or the frontend

## Example Response
```json
{
  "login": "octocat",
  "id": 583231,
  "name": "The Octocat",
  "public_repos": 8,
  "followers": 12345
}
```

## Next Steps
- Add caching for GitHub API calls
- Deploy to a hosting service (e.g., Render)

---
Built by Joseph Petrucci | March 2025