# app/api.py
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
import os
import json
from firebase_admin import auth

# Import our agents
from app.agents.main_agent import MainAgent
from app.agents.workflow_agent import WorkflowAgent
from app.services.firebase.firebase_service import initialize_firebase

# Initialize Firebase
initialize_firebase()

# Initialize agents
main_agent = MainAgent()
workflow_agent = WorkflowAgent(profile_service)

# Create the FastAPI app
app = FastAPI()

# Define the request body models
class ChatRequest(BaseModel):
    message: str

# Function to verify Firebase auth token
async def verify_token(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify the token and get user info
        decoded_token = auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Chat endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(verify_token)):
    try:
        # Process message through main agent
        main_response = await main_agent.process(user_id, request.message)
        
        # If workflow is profile, route to profile workflow agent
        if main_response.get("workflow") == "profile":
            workflow_response = await workflow_agent.process({
                "user_id": user_id,
                "action": main_response.get("action", "view"),
                "context": main_response.get("context", ""),
                "message": request.message
            })
            return workflow_response
        
        # For other workflows or general conversation, return main agent response
        return {"response": main_response.get("response")}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/")
async def root_health_check():
    return {"status": "healthy"}

# Additional health check endpoint at /health
@app.get("/health")
async def health_check():
    return {"status": "healthy"}