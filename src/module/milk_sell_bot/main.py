import asyncio
from src.core.agent.client import AgentWithMCP
from src.utils.loader.mcp_loader import load_mcp_client
from dotenv import load_dotenv
from jinja2 import Template
from src.core.memory.memory_manager import MemoryManager

load_dotenv()

system_prompt = Template(open("src/module/milk_sell_bot/prompts/sql_query.j2").read()).render()


async def main():
    # Init memory manager
    memory_manager = MemoryManager()
    user_id = "1234567890"
    session_id = "1234567890"
    
    # Load MCP clients
    print("Loading MCP clients...")
    mcp_client = await load_mcp_client({
        "search_tools": {
            "transport": "streamable_http",
            "url": "http://localhost:9000/mcp"
        },
        # "semantic_rag_tools": {
        #     "transport": "streamable_http",
        #     "url": "http://localhost:9005/mcp"
        # },
        "auto_sale_tools": {
            "transport": "streamable_http",
            "url": "http://localhost:9002/mcp"
        },
    })
    tools = await mcp_client.get_tools()
    print(f"✓ Loaded {len(tools)} tools")
    
    # Initialize agent
    agent = AgentWithMCP(tools, system_prompt)
    print("✓ Agent initialized\n")
    
    # Chat loop
    print("=" * 60)
    print("Chatbot is ready! Type 'exit', 'quit', or 'q' to exit.")
    print("=" * 60)
    
    while True:
        try:
            # Get user input
            query = input("\nYou: ").strip()
            
            # Check exit conditions
            if query.lower() in ['exit', 'quit', 'q', '']:
                print("Goodbye!")
                break
            
            # Get conversation history (increase to 10 for better context understanding)
            conversation = memory_manager.get_memory_as_conversation(user_id, session_id, top_k=6)
            
            # Get response from agent
            print("Bot: ", end="", flush=True)
            response = await agent.run(conversation, query)
            print(response)
            
            # Save to memory
            memory_manager.save_memory(user_id=user_id, session_id=session_id, question=query, answer=response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())