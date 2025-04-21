from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import httpx
from urllib.parse import urlencode
from config import CLIENT_ID, REDIRECT_URI, TOKEN_URL, AUTH_URL

app = FastAPI()

SCOPES = [
    "system/Patient.read",
    "system/Observation.read",
    "system/MedicationRequest.read",
    "system/AllergyIntolerance.read",
    "system/Encounter.read",
]

@app.get("/")
def launch_auth():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": "123",
        "scope": " ".join(SCOPES)
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)

@app.get("/callback")
async def handle_callback(request:Request):
    code = request._query_params.get("code")
    print(code, "******************************************")
    if not code:
        return {"error": "Authorization code not provided."}

    async with httpx.AsyncClient() as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_response = await client.post(TOKEN_URL, data=data, headers=headers)
        print("------------------------------------")
        print(token_response.status_code, token_response.text)
        print("------------------------------------")
    if token_response.status_code == 200:
        token_data = token_response.json()
        return {
            "access_token": token_data.get("access_token"),
            "expires_in": token_data.get("expires_in"),
        }
    else:
        return {"error": token_response.text}

@app.get("/export/status")
async def check_bulk_status(job_status_url: str, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(job_status_url, headers=headers)

    if response.status_code == 202:
        return {"status": "In Progress"}
    elif response.status_code == 200:
        return {
            "status": "Completed",
            "output": response.json().get("output", []),
        }
    else:
        return {"error": response.text, "status_code": response.status_code}


