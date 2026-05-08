import os
from typing import List, Dict, Any
from fastapi import FastAPI
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(title="AI Analyzer API", version="1.0.0")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")

def get_mongo_client():
    return MongoClient(MONGO_URI)

def get_database():
    client = get_mongo_client()
    return client["ai_analyzer"]

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "AI Analyzer API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/results", response_model=List[Dict[str, Any]]])
def get_results(limit: int = 10):
    db = get_database()
    collection = db["results"]
    results = list(collection.find().sort("timestamp", -1).limit(limit))
    
    for result in results:
        if "_id" in result:
            result["_id"] = str(result["_id"])
        if "timestamp" in result and hasattr(result["timestamp"], "isoformat"):
            result["timestamp"] = result["timestamp"].isoformat()
    
    return results

@app.get("/health")
def health_check():
    try:
        db = get_database()
        db.command("ping")
        mongo_status = "connected"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "mongo": mongo_status,
        "timestamp": datetime.now().isoformat()
    }