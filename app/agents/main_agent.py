from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.memory import BaseMemory
from typing import Dict, Any, List, Tuple
import os
import json

class MainAgent:
    """Main interaction agent that handles general conversation and routes to specific workflows"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
            model_name="gpt-4-0125-preview"
        )
        self.chat_history: List[Tuple[str, str]] = []
        self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize the conversation chain with appropriate prompts"""
        template = """You are ParentPal's main assistant, responsible for helping users with various tasks and routing them to appropriate workflows.

Current conversation:
{chat_history}

Your primary responsibilities are:
1. Engage in general conversation with users
2. Identify what users and route them to specific workflows when needed
3. For now, the first workflow being implemented is the profile workflow.

PROFILE WORKFLOW TRIGGERS:
- First user sign-in.
- Explicit profile requests ("I want to update my profile", "How do I add my spouse?")
- Missing profile information for a task requested by the user.
- Profile completion reminders.

USER STATES TO TRACK:
1. New User
   - No profile information
   - Need to guide through initial setup
2. Incomplete Profile
   - Has some information
   - Missing critical fields
3. Complete Profile
   - All required information provided
   - May need updates

When profile workflow is needed, respond with:
{{
    "workflow": "profile",
    "action": "update_profile|add_spouse|add_child|view",
    "context": "reason for profile workflow",
    "response": "your conversational response"
}}

For general conversation, respond with:
{{
    "workflow": "general",
    "response": "your conversational response"
}}

User Input: {input}"""

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["chat_history", "input"]
        )
        
        # Create the chain using the pipe operator
        def format_history(x):
            return {
                "chat_history": "\n".join([f"Human: {h}\nAssistant: {a}" for h, a in self.chat_history]),
                "input": x["input"]
            }

        self.chain = format_history | self.prompt | self.llm
    
    async def process(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process user input and determine appropriate workflow"""
        try:
            # Run the chain
            response = await self.chain.ainvoke({"input": message})
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Update chat history
            self.chat_history.append((message, response_text))
            if len(self.chat_history) > 5:  # Keep last 5 exchanges
                self.chat_history.pop(0)
            
            # Parse the response
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If response isn't valid JSON, wrap it in a basic structure
                response_data = {
                    "workflow": "general",
                    "response": response_text
                }
            
            # Add user_id to response data
            response_data["user_id"] = user_id
            
            # Handle profile workflow responses
            if response_data["workflow"] == "profile":
                # Ensure action is one of the valid options
                valid_actions = {"update_profile", "add_spouse", "add_child", "view"}
                current_action = response_data.get("action", "")
                
                # For new users or invalid actions, default to update_profile
                if not current_action or current_action not in valid_actions:
                    response_data["action"] = "update_profile"
                    response_data["context"] = "New user sign-in"
                    response_data["response"] = "Welcome to ParentPal! I'm thrilled to have you with us. Let's get started on setting up your profile. This will help us tailor your experience and provide you with the most relevant information and suggestions. If you need any help along the way, just let me know!"
            
            return response_data
            
        except Exception as e:
            return {
                "workflow": "error",
                "error": str(e),
                "user_id": user_id
            } 