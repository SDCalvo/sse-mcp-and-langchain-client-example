import asyncio
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Ensure your FastAPI server (main.py) is running!
# You might need to uncomment the greet_user endpoint in main.py and restart it.
mcp_config = {
    "local_fastapi": { # Give our server a name within the client config
        "url": "http://127.0.0.1:8000/mcp",  # URL of our running FastAPI MCP server
        "transport": "sse"                  # Use HTTP + SSE transport
        # Add "headers": {"Authorization": "Bearer <TOKEN>"} here if you add auth later
    }
}

# Configure the LLM (ensure OPENAI_API_KEY is set in your environment)
# You can replace this with ChatAnthropic or another supported model
llm = ChatOpenAI(model="gpt-4o") # Or another model like "gpt-3.5-turbo"

async def run_agent():
    print("Connecting to MCP server(s)...")
    async with MultiServerMCPClient(mcp_config) as client:
        print("Discovering tools...")
        tools = client.get_tools() # This fetches tools from all configured servers
        
        if not tools:
            print("Error: No tools discovered from the MCP server.")
            print("Ensure the server is running and fastapi-mcp is mounted AFTER route definitions.")
            return

        print(f"Discovered tools: {[tool.name for tool in tools]}")

        # Create the LangGraph ReAct Agent
        agent_executor = create_react_agent(llm, tools)
        print("Agent created. Ready for query.")

        # --- Test Queries ---
        # Query 1: Should use the read_root tool
        query1 = "What is the welcome message from the FastAPI server?"
        print(f"\nInvoking agent with query: '{query1}'")
        async for event in agent_executor.astream_events({"messages": [("user", query1)]}, version="v1"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # Print intermediate LLM output
                    print(content, end="|")
            elif kind == "on_tool_start":
                print("--")
                print(f"Calling tool '{event['name']}' with args {event['data'].get('input')}")
            elif kind == "on_tool_end":
                print(f"Tool '{event['name']}' finished.")
                print(f"Tool output: {event['data'].get('output')}")
                print("--")
            elif kind == "on_chain_end":
                 if event["name"] == "__main__": # End of main agent run
                     print("\nAgent finished.")
                     # print(f"Final Result: {event['data'].get('output')}") # Sometimes useful, sometimes redundant

        # Add more queries if needed, e.g., to test greet_user
        # query2 = "Greet the user 'LangChain'"
        # print(f"\nInvoking agent with query: '{query2}'")
        # result2 = await agent_executor.ainvoke({"messages": [("user", query2)]})
        # print(f"Result 2: {result2}")


if __name__ == "__main__":
    # Let ChatOpenAI handle the key loading from environment after load_dotenv
    try:
        asyncio.run(run_agent())
    except Exception as e:
        print(f"An error occurred during agent execution: {e}")
        # Specifically catch the OpenAIError if the key is still missing/invalid after loading .env
        if "api_key client option must be set" in str(e):
             print("Hint: Make sure OPENAI_API_KEY is defined correctly in your .env file.") 