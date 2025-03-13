from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings
from typing import Dict, Any, List, Optional, Union, Tuple, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
import logging
from ..models.profile_models import (
    UserProfile, SpouseProfile, ChildProfile,
    NameComponents, PersonProfile
)

logger = logging.getLogger(__name__)

class ProfileError(Exception):
    """Custom error class for profile-related errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details
        super().__init__(message)

class ProfileResponse(BaseModel):
    """Standardized response model for profile operations"""
    status: Literal["success", "needs_input", "error"]
    response: str
    data: Optional[Union[UserProfile, SpouseProfile, ChildProfile]] = None
    action: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict] = None

class ProfileAgentConfig(BaseSettings):
    """Configuration settings for the Profile Agent"""
    model: str = "gpt-4-turbo"
    temperature: float = 0.2
    max_history: int = 5
    
    class Config:
        env_prefix = "PROFILE_AGENT_"

class ProfileAgent:
    """Handles conversational interaction and structured data extraction for user profiles"""
    
    def __init__(self):
        """Initialize the profile agent with configuration"""
        self.config = ProfileAgentConfig()
        self.llm = ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature
        )
        self.chat_history: List[Tuple[str, str]] = []
    
    def _get_function_schema(self, action: str) -> dict:
        """Get the function schema for the given action."""
        base_schema = {
            "name": "extract_profile_data",
            "description": "Extract profile information from user input",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        if action == "update_profile":
            base_schema["parameters"]["properties"].update({
                "firstName": {"type": "string", "description": "User's first name"},
                "lastName": {"type": "string", "description": "User's last name"},
                "dateOfBirth": {"type": "string", "description": "User's date of birth in MM/DD/YYYY format"},
                "address": {"type": "string", "description": "User's full address"}
            })
            base_schema["parameters"]["required"] = ["firstName", "lastName"]
        elif action == "add_spouse":
            base_schema["parameters"]["properties"].update({
                "firstName": {"type": "string", "description": "Spouse's first name"},
                "lastName": {"type": "string", "description": "Spouse's last name"},
                "dateOfBirth": {"type": "string", "description": "Spouse's date of birth in MM/DD/YYYY format"}
            })
            base_schema["parameters"]["required"] = ["firstName", "lastName"]
        elif action == "add_child":
            base_schema["parameters"]["properties"].update({
                "firstName": {"type": "string", "description": "Child's first name"},
                "lastName": {"type": "string", "description": "Child's last name"},
                "dateOfBirth": {"type": "string", "description": "Child's date of birth in MM/DD/YYYY format"},
                "interests": {"type": "array", "items": {"type": "string"}, "description": "Child's interests"},
                "medicalConsiderations": {"type": "array", "items": {"type": "string"}, "description": "Child's medical considerations"}
            })
            base_schema["parameters"]["required"] = ["firstName", "lastName", "dateOfBirth"]
        
        return base_schema
    
    def _get_system_prompt(self, action: str) -> str:
        """Generate context-aware system prompt"""
        base_prompt = (
            "You are the ParentPal Profile Assistant, helping users provide their profile information "
            "in a natural, conversational way. Extract information only when users clearly provide it. "
            "When extracting information, use the provided function to structure the data in JSON format."
            "IMPORTANT: Maintain a warm, friendly, and conversational tone throughout. Avoid sounding "
            "robotic or form-like. Don't ask for information in a rigid sequence - flow naturally with "
            "the conversation. If a user shares a story or additional context, acknowledge it before "
            "continuing with profile collection.\n\n"
            "Examples of good responses:\n"
            "- \"Thanks for sharing that about your son! I've noted his interest in sports. Do you mind "
            "sharing his date of birth as well so I can provide age-appropriate advice?\"\n"
            "- \"I appreciate you telling me about your family! I've updated your profile with your name "
            "and address. Is there anything else you'd like to share?\"\n\n"
            "Always prioritize the conversation flow over data collection."
        )
        
        # Add action-specific context
        action_contexts = {
            "update_profile": "\n\nCollecting or updating basic profile information. Extract name (firstName, middleName, lastName), date of birth (MM/DD/YYYY), and address if provided.",
            "add_spouse": "\n\nCollecting spouse information. Extract name (firstName, middleName, lastName) and date of birth (MM/DD/YYYY) if provided.",
            "add_child": "\n\nCollecting child information. Extract name (firstName, middleName, lastName), date of birth (MM/DD/YYYY), interests (list), and medical considerations (list) if provided."
        }
        if action in action_contexts:
            base_prompt += action_contexts[action]
        
        base_prompt += "\n\nRespond in a conversational way and use the function to extract structured data in JSON format."
        
        return base_prompt
    
    async def process(self, message: str, action: str) -> dict:
        """Process a message and extract profile information."""
        logger.info(f"Profile Agent received message: '{message}'")
        logger.info(f"Profile Agent action: {action}")
        logger.info(f"Starting profile processing...")

        try:
            # Prepare conversation history
            messages = [
                SystemMessage(content=self._get_system_prompt(action)),
                HumanMessage(content=message)
            ]

            # Get function schema for the action
            function_schema = self._get_function_schema(action)

            # Before the LLM call
            logger.info(f"Calling LLM with function schema for action: {action}")
            logger.info(f"System prompt: {self._get_system_prompt(action)}")

            # Call LLM with function calling
            response = await self.llm.ainvoke(
                messages,
                functions=[function_schema],
                function_call={"name": "extract_profile_data"}
            )

            # After the LLM call
            logger.info(f"LLM response received")
            logger.info(f"Function call exists: {bool(response.additional_kwargs.get('function_call'))}")

            # Extract function call arguments
            if not response.additional_kwargs.get('function_call'):
                return {
                    'status': 'needs_input',
                    'response': "I couldn't extract the necessary information. Could you provide more details?",
                    'data': None,
                    'action': action,
                    'error': None,
                    'details': None
                }

            # Parse function call arguments
            extracted_data = json.loads(response.additional_kwargs['function_call']['arguments'])

            logger.info(f"Extracted data from LLM: {extracted_data}")
            logger.info(f"Required fields for {action}: {required_fields[action]}")
            logger.info(f"Missing fields: {missing_fields}")
            
            # Check if we have all required fields
            required_fields = {
                'update_profile': ['firstName', 'lastName', 'dateOfBirth', 'address'],
                'add_spouse': ['firstName', 'lastName', 'dateOfBirth'],
                'add_child': ['firstName', 'lastName', 'dateOfBirth']
            }
            
            missing_fields = [field for field in required_fields[action] if not extracted_data.get(field)]
            if missing_fields:
                return {
                    'status': 'needs_input',
                    'response': f"I need more information. Could you provide your {', '.join(missing_fields)}?",
                    'data': extracted_data,
                    'action': action,
                    'error': None,
                    'details': {'missing_fields': missing_fields}
                }
            
            # Validate data based on action
            try:
                if action == "update_profile":
                    logger.info("Validating profile data...")
                    name_components = NameComponents(
                        firstName=extracted_data.get('firstName'),
                        lastName=extracted_data.get('lastName')
                    )
                    profile_data = UserProfile(
                        name=name_components,
                        dateOfBirth=extracted_data.get('dateOfBirth'),
                        address=extracted_data.get('address')
                    )
                    return {
                        'status': 'success',
                        'response': "Great! I've got your profile information.",
                        'data': profile_data.model_dump(),
                        'action': action,
                        'error': None,
                        'details': None
                    }
                    logger.info("Profile data validation successful")
                elif action == "add_spouse":
                    name_components = NameComponents(
                        firstName=extracted_data.get('firstName'),
                        lastName=extracted_data.get('lastName')
                    )
                    spouse_data = SpouseProfile(
                        name=name_components,
                        dateOfBirth=extracted_data.get('dateOfBirth')
                    )
                    return {
                        'status': 'success',
                        'response': "I've recorded your spouse's information.",
                        'data': spouse_data.model_dump(),
                        'action': action,
                        'error': None,
                        'details': None
                    }
                elif action == "add_child":
                    name_components = NameComponents(
                        firstName=extracted_data.get('firstName'),
                        lastName=extracted_data.get('lastName')
                    )
                    child_data = ChildProfile(
                        name=name_components,
                        dateOfBirth=extracted_data.get('dateOfBirth'),
                        interests=extracted_data.get('interests', []),
                        medicalConsiderations=extracted_data.get('medicalConsiderations', [])
                    )
                    return {
                        'status': 'success',
                        'response': "I've recorded your child's information.",
                        'data': child_data.model_dump(),
                        'action': action,
                        'error': None,
                        'details': None
                    }
            except Exception as e:
                logger.error(f"Profile data validation failed: {str(e)}")
                return {
                    'status': 'error',
                    'response': "An unexpected error occurred while processing your request.",
                    'data': None,
                    'action': action,
                    'error': str(e),
                    'details': None
                }

        except ValidationError as e:
            return {
                'status': 'error',
                'response': "The provided information is not valid.",
                'data': None,
                'action': action,
                'error': str(e),
                'details': e.errors()
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'status': 'error',
                'response': "An unexpected error occurred while processing your request.",
                'data': None,
                'action': action,
                'error': str(e),
                'details': None
            } 