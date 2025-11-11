from dotenv import load_dotenv
import os 

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")



def convert_conversation_to_messages(conversation: List[Dict[str, Any]]):
    messages = []
    for message in conversation:
        if message["role"] == "user":
            messages.append(HumanMessage(content=message["content"]))
        elif message["role"] == "assistant":
            messages.append(AIMessage(content=message["content"]))
    return messages

def create_model():
    #  Check config is valid
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    if not OPENAI_BASE_URL:
        raise ValueError("OPENAI_BASE_URL is not set")
    if not OPENAI_MODEL:
        raise ValueError("OPENAI_MODEL is not set")

    return ChatOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, model=OPENAI_MODEL, temperature=0.3)


class AgentWithMCP:

    def __init__(self, tools: List[BaseTool], system_prompt: str):

        self.tools = tools
        self.model =  create_model()
        self.agent = create_react_agent(self.model, self.tools, prompt=system_prompt)


    async def run(self, conversation: List[Dict[str, Any]], query: str):
        # History conversation
        messages = convert_conversation_to_messages(conversation)
        # Query from the users 
        messages.append(HumanMessage(content=query))
        # LangGraph agent expects a dict with "messages" key
        result = await self.agent.ainvoke({"messages": messages})
        
        # Extract the last AIMessage content from the result
        result_messages = result.get("messages", [])
        # Find the last AIMessage (excluding tool calls)
        for message in reversed(result_messages):
            if isinstance(message, AIMessage) and message.content:
                return message.content
        
        # If no AIMessage with content found, return the last message
        if result_messages:
            last_message = result_messages[-1]
            if hasattr(last_message, 'content'):
                return last_message.content
        
        return result
