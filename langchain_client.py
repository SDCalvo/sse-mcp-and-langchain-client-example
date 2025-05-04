import asyncio
import json
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

load_dotenv()

# --- Configuration ---
# Ensure your FastAPI server (main.py) is running!
mcp_config = {
    "local_fastapi": { # Give our server a name within the client config
        "url": "http://127.0.0.1:8000/mcp",  # URL of our running FastAPI MCP server
        "transport": "sse",                  # Use HTTP + SSE transport
        # Add headers for authentication
        "headers": {
            "Authorization": "Bearer MY_SECRET_TOKEN" # Replace with your actual token mechanism
        }
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
        final_answer_q1 = ""
        all_events_q1 = [] # List to collect events for query 1
        async for event in agent_executor.astream_events({"messages": [("user", query1)]}, version="v1"):
            # Only process/collect events that are NOT chat model streams
            if event["event"] != "on_chat_model_stream":
                # Create a simplified version of the event for logging
                simplified_event = {
                    "event_type": event["event"],
                    "name": event.get("name", "Unknown") # Get name, provide default
                }
                
                if event["event"] == "on_tool_start":
                    simplified_event["input"] = event.get("data", {}).get("input")
                elif event["event"] == "on_tool_end":
                    output_data = event.get("data", {}).get("output")
                    try:
                        # Try to parse if it's a JSON string
                        if isinstance(output_data, str):
                            simplified_event["output"] = json.loads(output_data)
                        else:
                            simplified_event["output"] = output_data # Keep as is if not string
                    except (json.JSONDecodeError, TypeError):
                        # Fallback for non-JSON strings or other types
                        simplified_event["output(raw)"] = output_data 

                all_events_q1.append(simplified_event) # Collect the simplified event
            
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # print(content, end="|") # Commented out to reduce noise
                    final_answer_q1 += content # Still accumulate final answer
            elif kind == "on_tool_start":
                print("\n-- TOOL START --")
                print(f"Tool Name: {event['name']}")
                print(f"Tool Args: {json.dumps(event['data'].get('input'), indent=2)}") # Pretty print args
            elif kind == "on_tool_end":
                print("\n-- TOOL END --")
                print(f"Tool Name: {event['name']}")
                try:
                    # Handle potential non-string output before loading
                    output_data = event['data'].get('output')
                    if isinstance(output_data, str):
                        tool_output = json.loads(output_data)
                        print(f"Tool Output:\n{json.dumps(tool_output, indent=2)}")
                    else:
                        # If output isn't a string, print its representation
                        print(f"Tool Output (non-string): {output_data}") 
                except (json.JSONDecodeError, TypeError):
                     # Fallback for non-JSON string output
                     print(f"Tool Output (raw string): {event['data'].get('output')}")
                print("----------------")

        # ---- Print results AFTER the loop for Query 1 ----
        print("\n-- AGENT FINISHED Q1 --")
        print(f"Final Answer: {final_answer_q1}")
        print("\n-- Collected Events for Q1 --")
        try:
            print(json.dumps(all_events_q1, indent=2, default=str))
        except Exception as e:
            print(f"Could not serialize events: {e}")
        print("=======================\n")
        # ---- End printing results for Query 1 ----

        # Add more queries if needed, e.g., to test greet_user
        query2 = "Greet the user 'LangChain'"
        print(f"\nInvoking agent with query: '{query2}'")
        # We can still stream events for debugging, but let's focus on the final result for clarity
        result2 = await agent_executor.ainvoke({"messages": [("user", query2)]})

        print("\n-- AGENT FINISHED Q2 --")
        # Extract and print the final human query and AI response cleanly
        if result2 and 'messages' in result2 and len(result2['messages']) >= 2:
             # The last message is usually the final AI response
             final_ai_message = result2['messages'][-1]
             # The first message is the initial user query (sometimes useful context)
             # initial_user_message = result2['messages'][0] 
             print(f"Final AI Response: {final_ai_message.content}")
        else:
             print("Could not parse final result structure.")
             print(f"Raw Result 2: {result2}") # Fallback to raw print
        print("=======================\n")


if __name__ == "__main__":
    # Let ChatOpenAI handle the key loading from environment after load_dotenv
    try:
        asyncio.run(run_agent())
    except Exception as e:
        print(f"An error occurred during agent execution: {e}")
        # Specifically catch the OpenAIError if the key is still missing/invalid after loading .env
        if "api_key client option must be set" in str(e):
             print("Hint: Make sure OPENAI_API_KEY is defined correctly in your .env file.") 