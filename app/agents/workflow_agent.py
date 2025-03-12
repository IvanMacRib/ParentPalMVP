from typing import Dict, Any, Optional, Union
import json
import logging
from pydantic import BaseModel
from .profile_agent import ProfileAgent, ProfileResponse, ProfileError
from ..models.profile_models import UserProfile, SpouseProfile, ChildProfile

logger = logging.getLogger(__name__)

class WorkflowError(Exception):
    """Custom error class for workflow-related errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details
        super().__init__(message)

class ProfileStatus(BaseModel):
    """Model for profile status information"""
    exists: bool = False
    is_complete: bool = False
    missing_fields: list[str] = []
    profile_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class WorkflowResponse(BaseModel):
    """Standardized response model for workflow operations"""
    status: str
    response: str
    profile_status: ProfileStatus
    error: Optional[str] = None

class WorkflowAgent:
    """Manages the profile completion workflow"""
    
    def __init__(self, profile_service):
        self.profile_agent = ProfileAgent()
        self.profile_service = profile_service
    
    async def get_profile_status(self, user_id: str) -> Dict[str, Any]:
        """Get current profile status and completion information"""
        try:
            logger.info(f"Getting profile status for user: {user_id}")
            # Get profile data from service
            profile = self.profile_service.getUserProfile(user_id)
            completion_status = self.profile_service.getProfileCompletionStatus(user_id)
            
            return ProfileStatus(
                exists=profile.get("exists", False),
                is_complete=completion_status.get("isComplete", False),
                missing_fields=completion_status.get("missingFields", []),
                profile_data=profile
            ).model_dump()
        except Exception as e:
            logger.error(f"Error getting profile status: {str(e)}")
            return ProfileStatus(error=str(e)).model_dump()
    
    async def process(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a profile workflow request"""
        try:
            user_id = workflow_data["user_id"]
            action = workflow_data.get("action", "view")
            message = workflow_data.get("message", "")
            
            logger.info(f"Processing workflow request for user: {user_id}")
            logger.info(f"Action: {action}, Message: {message}")
            
            # Get current profile status
            status = await self.get_profile_status(user_id)
            
            # Handle profile viewing
            if action == "view":
                return await self._handle_view_profile(user_id, status)
            
            # Process the message through profile agent
            agent_response = await self.profile_agent.process(message, action)
            
            logger.info(f"Profile agent response: {agent_response}")
            
            # If data was extracted, update the profile
            if agent_response["status"] == "success" and agent_response["data"]:
                await self._update_profile(
                    user_id, 
                    agent_response["data"], 
                    agent_response["action"] or action
                )
                
                # Get updated status
                new_status = await self.get_profile_status(user_id)
                
                return {
                    "status": "success",
                    "response": agent_response["response"],
                    "profile_status": new_status,
                    "error": None
                }
            
            # Otherwise, return the agent response
            return {
                "status": agent_response["status"],
                "response": agent_response["response"],
                "profile_status": status,
                "error": agent_response.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error processing workflow: {str(e)}")
            return {
                "status": "error",
                "response": "An error occurred while processing your request.",
                "profile_status": status if 'status' in locals() else await self.get_profile_status(user_id),
                "error": str(e)
            }
    
    async def _handle_view_profile(self, user_id: str, status: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a request to view profile information"""
        try:
            logger.info(f"Handling view profile request for user: {user_id}")
            
            if status.get("error"):
                raise WorkflowError("Error retrieving profile status", {"error": status["error"]})
            
            # Generate appropriate response based on profile status
            if not status.get("exists", False):
                response = "I see you haven't set up your profile yet. Would you like to create one now?"
            elif not status.get("is_complete", False):
                missing = ", ".join(status.get("missing_fields", []))
                response = f"Your profile is incomplete. The following information is missing: {missing}. Would you like to add this information?"
            else:
                response = "Your profile is complete! Let me know if you'd like to view or update any information."
            
            return {
                "status": "success",
                "response": response,
                "profile_status": status,
                "error": None
            }
        except WorkflowError as e:
            logger.error(f"Workflow error in view profile: {str(e)}")
            return {
                "status": "error",
                "response": "There was an issue retrieving your profile information.",
                "profile_status": status,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error handling view profile: {str(e)}")
            return {
                "status": "error",
                "response": "An unexpected error occurred while viewing your profile.",
                "profile_status": status,
                "error": str(e)
            }
    
    async def _update_profile(
        self, 
        user_id: str, 
        data: Union[Dict[str, Any], UserProfile, SpouseProfile, ChildProfile], 
        action: str
    ) -> None:
        """Update profile with validated data"""
        try:
            logger.info(f"Updating profile for user: {user_id}")
            logger.info(f"Action: {action}")
            logger.info(f"Data: {data}")
            
            # Convert data to dictionary if it's a Pydantic model
            data_dict = data.dict() if hasattr(data, 'dict') else data
            
            if action == "update_profile":
                self.profile_service.updateUserProfile(user_id, data_dict)
            elif action == "add_spouse":
                self.profile_service.addSpouse(user_id, data_dict)
            elif action == "add_child":
                self.profile_service.addChild(user_id, data_dict)
            elif action == "update_child":
                child_id = data_dict.pop("childId", None)
                if child_id:
                    self.profile_service.updateChild(user_id, child_id, data_dict)
                else:
                    raise WorkflowError("Missing child ID for update operation")
            else:
                raise WorkflowError(f"Unknown action: {action}")
                
            logger.info("Profile update successful")
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            raise WorkflowError(f"Failed to update profile: {str(e)}") 