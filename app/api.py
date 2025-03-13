# app/api.py
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
import os
import json
import logging
from firebase_admin import auth

# Import our agents
from app.agents.main_agent import MainAgent
from app.agents.workflow_agent import WorkflowAgent
from app.services.firebase.firebase_service import initialize_firebase
from app.services.firebase.profile_services import profile_service

# Initialize Firebase
initialize_firebase()

# Initialize agents
main_agent = MainAgent()
workflow_agent = WorkflowAgent(profile_service)

# Create the FastAPI app
app = FastAPI()

# Set up logger
logger = logging.getLogger(__name__)
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
        logger.info(f"Chat request received for user: {user_id}")
        logger.info(f"Message: {request.message}")
        
        # Process message through main agent
        logger.info("Passing message to main agent")
        main_response = await main_agent.process(user_id, request.message)
        logger.info(f"Main agent response: {main_response}")
        
        # If workflow is profile, route to profile workflow agent
        logger.info(f"Checking if workflow is profile, current workflow: {main_response.get('workflow')}")
        if main_response.get("workflow") == "profile":
            logger.info("WORKFLOW IS PROFILE - Routing to profile workflow")
            logger.info(f"Routing to profile workflow with action: {main_response.get('action', 'view')}")
            workflow_response = await workflow_agent.process({
                "user_id": user_id,
                "action": main_response.get("action", "view"),
                "context": main_response.get("context", ""),
                "message": request.message
            })
            logger.info(f"Profile workflow response: {workflow_response}")
            return workflow_response
        
        # For other workflows or general conversation, return main agent response
        logger.info("Returning main agent response")
        return {"response": main_response.get("response")}
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

#Status endpoinp

@app.get("/profile/status")
async def profile_status_endpoint(user_id: str = Depends(verify_token)):
    try:
        logger.info(f"Profile status check for user: {user_id}")
        profile_status = await workflow_agent.get_profile_status(user_id)
        logger.info(f"Profile status result: {profile_status}")
        
        return {
            "exists": profile_status.get("exists", False),
            "isComplete": profile_status.get("is_complete", False),
            "missingFields": profile_status.get("missing_fields", [])
        }
    except Exception as e:
        logger.error(f"Error checking profile status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/")
async def root_health_check():
    return {"status": "healthy"}

# Additional health check endpoint at /health
@app.get("/health")
async def health_check():
    return {"status": "healthy"}