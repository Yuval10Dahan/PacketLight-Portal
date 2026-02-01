import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict, Any
import alm_client
from alm_client import ALMClient

# Load environment variables
load_dotenv()

app = FastAPI(title="ALM Dashboard API")

# CORS (Cross-Origin Resource Sharing)
# Allowing all origins for development convenience. In production, restrict this.
origins = [
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from env
ALM_BASE_URL = os.getenv("ALM_BASE_URL")
ALM_DOMAIN = os.getenv("ALM_DOMAIN")
ALM_PROJECT = os.getenv("ALM_PROJECT")
ALM_USER = os.getenv("ALM_USER")
ALM_PASSWORD = os.getenv("ALM_PASSWORD")
ROOT_FOLDER_ID = int(os.getenv("ROOT_FOLDER_ID", "101"))

# Dependency to get ALM Client
def get_alm_client():
    if not ALM_BASE_URL or not ALM_USER:
        raise HTTPException(status_code=500, detail="ALM Configuration missing in .env")
    
    client = ALMClient(ALM_BASE_URL, ALM_DOMAIN, ALM_PROJECT)
    # In a real app, you'd manage session persistence/tokens better (e.g., singleton or cached)
    # For now, we authenticate on every request or assume session reuse if we enhanced the client.
    # To avoid re-auth spam, let's try to auth once or manage it. 
    # For this dashboard implementation: simple auth per request or reused instance if global.
    
    if not client.authenticate(ALM_USER, ALM_PASSWORD):
        raise HTTPException(status_code=401, detail="Failed to authenticate with ALM")
        
    return client

@app.get("/")
def read_root():
    return {"message": "ALM Dashboard API is running"}

@app.get("/api/dashboard/stats/{folder_id}")
def get_stats(folder_id: int, client: ALMClient = Depends(get_alm_client)):
    try:
        data = client.get_dashboard_stats(folder_id)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/devices")
def get_devices(client: ALMClient = Depends(get_alm_client)):
    """
    Get all folders starting with 'PL'
    """
    try:
        return client.get_pl_device_folders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/devices/{folder_id}/versions")
def get_versions(folder_id: int, client: ALMClient = Depends(get_alm_client)):
    """
    Get children of a specific device folder (treated as versions)
    """
    try:
        return client.get_children_folders(folder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
def get_config():
    """
    Returns public config like the root folder ID for the frontend to start with.
    """
    return {
        "root_folder_id": ROOT_FOLDER_ID
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
