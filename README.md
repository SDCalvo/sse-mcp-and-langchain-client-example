# FastAPI MCP Server + LangChain Client Example

> Example project demonstrating how to expose FastAPI endpoints as Model Context Protocol (MCP) tools using `fastapi-mcp`. Includes a basic LangChain agent (`langchain_client.py`) that connects to the local FastAPI server via HTTP/SSE using `langchain-mcp-adapters` to discover and use the exposed tools.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python:** Version 3.10 or higher recommended.
- **`uv`:** The Python package manager used in this project. ([Installation Instructions](https://astral.sh/uv#installation))
- **Node.js and npm:** Required for `npx` (used to run the optional MCP Inspector). You can download Node.js (which includes npm) from [nodejs.org](https://nodejs.org/).
- **Git:** For cloning the repository.
- **OpenAI API Key:** Required for the LangChain client example. You need to set this in a `.env` file.

This project demonstrates setting up a basic FastAPI application and exposing its endpoints as Model Context Protocol (MCP) tools using the `fastapi-mcp` library. It also includes a LangChain agent client that connects to and uses these tools, and covers configuring Cursor to connect as well.

## Getting Started / How to Run

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-directory>
    ```
2.  **Install `uv`:** If you don't have it, install the `uv` package manager (see [Project Setup](#project-setup) below for command).
3.  **Set up Environment & Install Dependencies:**
    ```bash
    uv init # If pyproject.toml doesn't exist
    uv venv # Create virtual environment (.venv)
    # Install all project dependencies
    uv pip install fastapi "uvicorn[standard]" fastapi-mcp langchain-mcp-adapters langgraph langchain-openai python-dotenv
    ```
4.  **Create `.env` File:** Create a file named `.env` in the project root directory and add your OpenAI API key:
    ```dotenv
    OPENAI_API_KEY=your_openai_api_key_here
    ```
5.  **Run the FastAPI MCP Server:** Open a terminal and run:
    ```bash
    uvicorn main:app --reload --port 8000
    ```
    Keep this terminal running.
    _(Alternatively, you can use the `Python: FastAPI MCP` debug configuration defined in `.vscode/launch.json` within VS Code / Cursor to run the server with the debugger attached.)_
6.  **Run the LangChain Client:** Open a _second_ terminal and run:

    ```bash
    uv run python langchain_client.py
    ```

    The client will connect to the server, discover tools, and run a query using the agent.

7.  **(Optional) Test Server with MCP Inspector:** Before running the LangChain client, or for more direct testing, you can use the official MCP Inspector tool:

    - Ensure the FastAPI server is running (Step 5).
    - Open another terminal and run: `npx @modelcontextprotocol/inspector`
      _(`npx` comes with Node.js/npm. If this command fails, ensure Node.js is installed and accessible in your PATH.)_
    - In the inspector UI, connect to your server URL: `http://127.0.0.1:8000/mcp`
    - Navigate to "Tools", click "List Tools" to see `read_root__get` and `greet_user_greet__name__get`.
    - Select a tool, fill parameters (e.g., `name` for greet_user), and click "Run Tool".

8.  **(Optional) Test `greet_user` with LangChain Client:** The `greet_user` endpoint and the corresponding test query (`query2`) in `langchain_client.py` are currently active. Simply run the LangChain client (Step 6) and observe the second part of its execution where it should attempt to greet the user 'LangChain'.
    - _(If you want to disable this test, comment out the `@app.get("/greet/{name}")` endpoint in `main.py` and the `query2` section in `langchain_client.py`)_

## Goal

To build a simple FastAPI server with MCP capabilities for learning and testing purposes, runnable locally and connectable from MCP clients like the Cursor editor's agent.

## Project Setup

1.  **Package Manager:** We used `uv`, a fast Python package installer and resolver written in Rust.
    - Installation (Windows PowerShell): `irm https://astral.sh/uv/install.ps1 | iex`
    - Project Initialization: `uv init` (Creates `pyproject.toml`)
    - Virtual Environment: `uv venv` (Creates and manages `.venv`)
2.  **Dependencies:** Installed using `uv`:
    ```bash
    # Specific commands used during development (covered by the combined install in Getting Started):
    # uv pip install fastapi "uvicorn[standard]" fastapi-mcp
    # uv pip install langchain-mcp-adapters langgraph langchain-openai python-dotenv
    ```
    This installs FastAPI, the Uvicorn ASGI server, `fastapi-mcp`, LangChain components, and `python-dotenv` into the `.venv` virtual environment.

## Application (`main.py`)

A simple FastAPI app was created with endpoints:

- `/`: Returns a welcome message.
- `/greet/{name}`: Returns a personalized greeting (currently commented out).

Crucially, the `fastapi-mcp` integration happens **after** the FastAPI route definitions:

```python
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

app = FastAPI(...)

# --- Define FastAPI routes (@app.get, @app.post, etc.) ---
@app.get("/")
async def read_root():
    # ... endpoint logic ...

# --- Initialize and mount fastapi-mcp AFTER routes ---
mcp = FastApiMCP(app)
mcp.mount() # Exposes tools under /mcp by default
```

## Running the Server

- **Directly:** `uvicorn main:app --reload --port 8000`
- **With Debugger (Cursor/VS Code):** A `launch.json` file was created in `.vscode` to run the app with the debugger attached.

## LangChain Client (`langchain_client.py`)

- Reads the `.env` file for the `OPENAI_API_KEY`.
- Uses `langchain-mcp-adapters` (`MultiServerMCPClient`) to connect to the running FastAPI server at `http://127.0.0.1:8000/mcp` via SSE.
- Automatically discovers tools exposed by the MCP server.
- Creates a LangGraph ReAct agent using the discovered tools and an OpenAI LLM.
- Runs a sample query through the agent.

## Cursor Integration (MCP Client)

1.  **Configuration:** A `.cursor/mcp.json` file was created in the project root:
    ```json
    {
      "mcpServers": {
        "local-fastapi-mcp": {
          "url": "http://127.0.0.1:8000/mcp"
        }
      }
    }
    ```
2.  **Activation:** The server needs to be enabled in Cursor's settings (Ctrl+, search for "Cursor Settings" and go to the "MCP" tab).
3.  **Usage:** The Cursor agent (in the chat panel) can then be asked to use the discovered tools.

## Key Learnings

- **`uv` Basics:** `uv init`, `uv venv`, and `uv pip install` provide a fast way to set up a Python project environment.
- **`fastapi-mcp` Initialization Order:** The `FastApiMCP(app)` instance must be created and `mcp.mount()` must be called _after_ the FastAPI routes (`@app.get`, etc.) that you want to expose as tools are defined. Otherwise, the tools won't be discovered.
- **Port Conflicts:** Background processes (like `uvicorn`) can hold ports. On Windows, `netstat -ano | findstr "<PORT>"` can find the Process ID (PID), and `taskkill /F /PID <PID>` can terminate it. Sometimes a short wait or restarting the IDE is needed for the OS to fully release the port.
- **Cursor MCP Configuration:** Using the `url` key in `.cursor/mcp.json` connects Cursor to HTTP-based MCP servers (like the one provided by `fastapi-mcp`).
- **Agent Tool Invocation:** While the general Cursor agent environment uses the configured MCP servers, the specific pair-programming AI assistant interacts with them using automatically generated internal names (e.g., `mcp_local-fastapi-mcp_read_root__get`) rather than a generic tool-calling function. Explicitly asking the agent in chat to "Use the tool..." works once the connection is established and the tool is discovered.

## Further Exploration & Features (from fastapi-mcp docs)

This section summarizes features and concepts from the `fastapi-mcp` documentation that we haven't implemented yet but are useful to know.

### Authentication & Authorization

`fastapi-mcp` supports using FastAPI dependencies for auth and also includes OAuth 2 support.

**Basic Token Passthrough:**

- No special server config needed initially.
- The MCP client needs to send the `Authorization` header. This can often be done via a bridge like `mcp-remote`:
  ```json
  {
    "mcpServers": {
      "remote-example": {
        "command": "npx",
        "args": [
          "mcp-remote",
          "http://localhost:8000/mcp",
          "--header",
          "Authorization:${AUTH_HEADER}"
        ]
      },
      "env": {
        "AUTH_HEADER": "Bearer <your-token>"
      }
    }
  }
  ```
- To _require_ auth on the MCP server side, add dependencies to `AuthConfig`:

  ```python
  from fastapi import Depends
  from fastapi_mcp import FastApiMCP, AuthConfig

  # Assuming verify_auth is your FastAPI dependency that checks the token
  mcp = FastApiMCP(
      app,
      auth_config=AuthConfig(
          dependencies=[Depends(verify_auth)],
      ),
  )
  ```

**OAuth 2 Flow:**

- Full support for OAuth 2 (MCP Spec 2025-03-26).
- Requires configuring `AuthConfig` with provider details (issuer, URLs, client ID/secret).
- `setup_proxies=True` is often needed to handle incompatibilities between standard OAuth providers and MCP client expectations (like missing dynamic registration, scope handling).
  ```python
  mcp = FastApiMCP(
      app,
      auth_config=AuthConfig(
          issuer=f"https://auth.example.com/",
          authorize_url=f"https://auth.example.com/authorize",
          oauth_metadata_url=f"https://auth.example.com/.well-known/oauth-authorization-server",
          audience="my-audience",
          client_id="my-client-id",
          client_secret="my-client-secret",
          dependencies=[Depends(verify_auth)],
          setup_proxies=True, # Creates compatibility endpoints
      ),
  )
  ```
- Using `mcp-remote` often requires specifying a fixed port (`mcp-remote ... 8080`) so the callback URL (`http://127.0.0.1:8080/oauth/callback`) can be configured in the OAuth provider.

### Tool Naming

- MCP tool names are derived from the FastAPI route's `operation_id`.
- If not specified, FastAPI generates one automatically (e.g., `read_user_users__user_id__get`).
- It's **recommended** to set explicit `operation_id`s on FastAPI routes for clearer MCP tool names:
  ```python
  @app.get("/users/{user_id}", operation_id="get_user_info")
  async def read_user(user_id: int):
      # ...
  ```

### Refreshing Tools

- If FastAPI routes are added _after_ `mcp.mount()` is called, they won't be automatically included.
- Solution: Call `mcp.setup_server()` again after defining the new routes.

  ```python
  app = FastAPI()
  mcp = FastApiMCP(app)
  mcp.mount()

  @app.get("/new/endpoint", operation_id="new_tool")
  async def new_endpoint(): ...

  # Refresh the tools
  mcp.setup_server()
  ```

### Testing

- The `@modelcontextprotocol/inspector` tool can be used to test MCP servers:
  ```bash
  # Run the inspector
  npx @modelcontextprotocol/inspector
  # Connect to your server URL (e.g., http://127.0.0.1:8000/mcp)
  # Use the UI to list and run tools.
  ```

### Deployment

- You can mount the MCP server created from one FastAPI app (`api_app`) onto a _different_ FastAPI app (`mcp_app`) for separate deployment:

  ```python
  api_app = FastAPI()
  # ... define API endpoints ...

  mcp_app = FastAPI()
  mcp = FastApiMCP(api_app) # Create from api_app
  mcp.mount(mcp_app) # Mount onto mcp_app

  # Run separately:
  # uvicorn main:api_app --port 8001
  # uvicorn main:mcp_app --port 8000
  ```

### Customization

- Server name/description can be set during `FastApiMCP` initialization:
  ```python
  mcp = FastApiMCP(
      app,
      name="My Custom MCP Name",
      description="Description for the server."
  )
  ```
- Tool/schema descriptions can be customized (e.g., include all possible responses):
  ```python
  mcp = FastApiMCP(
      app,
      describe_all_responses=True,
      describe_full_response_schema=True
  )
  ```
- Exposed endpoints can be filtered using `include_operations`, `exclude_operations`, `include_tags`, `exclude_tags` during `FastApiMCP` initialization.
