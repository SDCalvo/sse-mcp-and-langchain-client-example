from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

app = FastAPI(title="MCP FastAPI Server", version="0.1.0")

@app.get("/")
async def read_root():
    """Returns a simple welcome message."""
    return {"message": "Welcome to the FastAPI MCP Server!"}

@app.get("/greet/{name}")
async def greet_user(name: str):
    """Greets the user by name."""
    return {"message": f"Hello, {name}!"}


# ADD MCP setup AFTER endpoints
mcp = FastApiMCP(app)
mcp.mount()
