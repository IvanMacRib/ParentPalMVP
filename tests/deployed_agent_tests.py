import asyncio
import logging
import json
import aiohttp
import os
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Cloud Run service URL
DEPLOYED_SERVICE_URL = "https://parentpal-api-132408711318.us-central1.run.app"

# Use a consistent test user ID
TEST_USER_ID = "test_user_123"  # TODO: Replace with actual test user ID

async def validate_response(response: dict, context: str) -> bool:
    """Validate that the response is meaningful and properly structured."""
    if not isinstance(response, dict):
        raise ValueError(f"Invalid response format: {response}")
    if "response" not in response:
        raise ValueError(f"Response missing 'response' field: {response}")
    logger.info(f"Response validation passed for {context}")
    return True

async def send_chat_request(session: aiohttp.ClientSession, message: str, auth_token: str) -> Dict[str, Any]:
    """Send a chat request to the deployed service."""
    url = f"{DEPLOYED_SERVICE_URL}/chat"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    payload = {"message": message}
    
    async with session.post(url, json=payload, headers=headers) as response:
        if response.status != 200:
            error_text = await response.text()
            raise ValueError(f"Request failed with status {response.status}: {error_text}")
        return await response.json()

async def test_deployed_agents(auth_token: str):
    """
    Run a series of tests against the deployed agent system.
    Tests both main agent routing and profile workflow.
    """
    logger.info("=== Starting Deployed Agent System Tests ===")

    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Basic greeting through main agent
            logger.info("1. Testing main agent greeting")
            response = await send_chat_request(session, "Hi, I'm new here!", auth_token)
            await validate_response(response, "main agent greeting")
            logger.info(f"Response: {response}")
            assert response["workflow"] == "profile", "New user should be routed to profile workflow"

            # Test 2: Profile workflow - Adding basic profile information
            logger.info("2. Testing profile workflow - basic info")
            response = await send_chat_request(
                session,
                "My name is John Smith. I was born on March 15, 1980, and I live at 123 Main St, Springfield, IL 62701.",
                auth_token
            )
            await validate_response(response, "profile creation")
            logger.info(f"Response: {response}")

            # Test 3: Profile workflow - Adding spouse
            logger.info("3. Testing profile workflow - adding spouse")
            response = await send_chat_request(
                session,
                "My wife's name is Jane Smith and she was born on May 15, 1985.",
                auth_token
            )
            await validate_response(response, "spouse addition")
            logger.info(f"Response: {response}")

            # Test 4: Profile workflow - Adding child
            logger.info("4. Testing profile workflow - adding child")
            response = await send_chat_request(
                session,
                "I want to add my son Tommy Smith. He was born on January 15, 2019. He loves sports and reading, and we need to note that he has a peanut allergy.",
                auth_token
            )
            await validate_response(response, "child addition")
            logger.info(f"Response: {response}")

            # Test 5: Profile workflow - Checking status
            logger.info("5. Testing profile workflow - status check")
            response = await send_chat_request(
                session,
                "Is my profile complete?",
                auth_token
            )
            await validate_response(response, "status check")
            logger.info(f"Response: {response}")

            # Test 6: Main agent - General conversation
            logger.info("6. Testing main agent - general conversation")
            response = await send_chat_request(
                session,
                "What can you help me with?",
                auth_token
            )
            await validate_response(response, "general conversation")
            logger.info(f"Response: {response}")

            logger.info("=== Deployed Agent System Tests Completed Successfully ===")
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get auth token from environment
    auth_token = os.getenv("FIREBASE_AUTH_TOKEN")
    if not auth_token:
        raise ValueError("FIREBASE_AUTH_TOKEN environment variable is required")
    
    asyncio.run(test_deployed_agents(auth_token)) 