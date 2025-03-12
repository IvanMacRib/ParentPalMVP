import asyncio
import logging
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.agents.main_agent import MainAgent
from app.agents.workflow_agent import WorkflowAgent
from app.services.firebase.firebase_service import initialize_firebase
from app.services.firebase.profile_services import ProfileService

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Firebase
initialize_firebase()

# Initialize services and agents
profile_service = ProfileService()
main_agent = MainAgent()
workflow_agent = WorkflowAgent(profile_service)

# Use a consistent test user ID
TEST_USER_ID = "test_user_123"  # TODO: Replace with actual test user ID

async def validate_response(response: dict, context: str) -> bool:
    """Validate that the response is meaningful and properly structured."""
    if not isinstance(response, dict):
        raise ValueError(f"Invalid response format - not a dictionary: {response}")
    
    # For workflow responses
    if "status" in response:
        if response["status"] == "error":
            logger.error(f"Error in response: {response.get('error', 'Unknown error')}")
            return False
        if response["status"] not in ["success", "needs_input"]:
            raise ValueError(f"Invalid status: {response['status']}")
        if "response" not in response or "profile_status" not in response:
            raise ValueError(f"Invalid workflow response format - missing required fields: {response}")
        
        # For successful profile updates
        if response["status"] == "success":
            profile_status = response["profile_status"]
            if not profile_status.get("exists", False):
                raise ValueError(f"Profile should exist after successful update: {response}")
            if not profile_status.get("profile_data", {}).get("exists", False):
                raise ValueError(f"Profile data should exist after successful update: {response}")
            profile = profile_status.get("profile_data", {}).get("profile", {})
            if not profile:
                raise ValueError(f"Profile data should contain profile information: {response}")
    # For main agent responses
    else:
        if "response" not in response and "error" not in response:
            raise ValueError(f"Response missing 'response' or 'error' field: {response}")
        if "workflow" not in response:
            raise ValueError(f"Response missing 'workflow' field: {response}")
    
    logger.info(f"Response validation passed for {context}")
    return True

async def test_agents():
    """
    Run a series of tests for the agent system.
    Tests both main agent routing and profile workflow.
    """
    logger.info("=== Starting Agent System Tests ===")

    try:
        # Test 1: Basic greeting through main agent
        logger.info("1. Testing main agent greeting")
        response = await main_agent.process(TEST_USER_ID, "Hi, I'm new here!")
        await validate_response(response, "main agent greeting")
        logger.info(f"Response: {response}")
        assert response["workflow"] == "profile", "New user should be routed to profile workflow"

        # Test 2: Profile workflow - Adding basic profile information
        logger.info("2. Testing profile workflow - basic info")
        workflow_response = await workflow_agent.process({
            "user_id": TEST_USER_ID,
            "action": "update_profile",
            "context": "new user",
            "message": "My name is John Smith. I was born on March 15, 1980, and I live at 123 Main St, Springfield, IL 62701."
        })
        await validate_response(workflow_response, "profile creation")
        logger.info(f"Response: {workflow_response}")

        # Test 3: Profile workflow - Adding spouse
        logger.info("3. Testing profile workflow - adding spouse")
        workflow_response = await workflow_agent.process({
            "user_id": TEST_USER_ID,
            "action": "add_spouse",
            "context": "adding spouse",
            "message": "My wife's name is Jane Smith and she was born on May 15, 1985."
        })
        await validate_response(workflow_response, "spouse addition")
        logger.info(f"Response: {workflow_response}")

        # Test 4: Profile workflow - Adding child
        logger.info("4. Testing profile workflow - adding child")
        workflow_response = await workflow_agent.process({
            "user_id": TEST_USER_ID,
            "action": "add_child",
            "context": "adding child",
            "message": "I want to add my son Tommy Smith. He was born on January 15, 2019. He loves sports and reading, and we need to note that he has a peanut allergy."
        })
        await validate_response(workflow_response, "child addition")
        logger.info(f"Response: {workflow_response}")

        # Test 5: Profile workflow - Checking status
        logger.info("5. Testing profile workflow - status check")
        workflow_response = await workflow_agent.process({
            "user_id": TEST_USER_ID,
            "action": "view",
            "context": "checking status",
            "message": "Is my profile complete?"
        })
        await validate_response(workflow_response, "status check")
        logger.info(f"Response: {workflow_response}")

        # Test 6: Main agent - General conversation
        logger.info("6. Testing main agent - general conversation")
        response = await main_agent.process(TEST_USER_ID, "What can you help me with?")
        await validate_response(response, "general conversation")
        logger.info(f"Response: {response}")

        logger.info("=== Agent System Tests Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    finally:
        # TODO: Add cleanup code here if needed
        # For example, resetting the test user's profile data
        pass

if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(test_agents()) 