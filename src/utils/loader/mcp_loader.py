from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Dict

async def load_mcp_client(tools:Dict):
    client = MultiServerMCPClient(tools)
    return client

