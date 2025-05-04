from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi_mcp import FastApiMCP
from typing import Annotated # Use Annotated for Header dependency

# --- Authentication Dependency ---
async def verify_token(authorization: Annotated[str | None, Header()] = None):
    """Checks for a valid Bearer token in the Authorization header."""
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
        
    token = parts[1]
    # --- Replace with your actual token validation logic --- 
    if token != "MY_SECRET_TOKEN": 
        raise HTTPException(status_code=403, detail="Invalid token")
    # --- End of validation logic --- 
    
    print(f"Successfully authenticated with token: {token[:5]}...") # Log for confirmation
    return {"token": token} # Optionally return validated data

# --- End Authentication Dependency ---

app = FastAPI(title="MCP FastAPI Server", version="0.1.0")

@app.get("/", operation_id="get_welcome_message")
async def read_root():
    """Returns a simple welcome message."""
    return {"message": "Welcome to the FastAPI MCP Server!"}

@app.get("/greet/{name}", operation_id="greet_named_user")
async def greet_user(name: str, token_data: dict = Depends(verify_token)):
    """Greets the user by name. Requires authentication."""
    # token_data contains {'token': 'MY_SECRET_TOKEN'} if verification passed
    print(f"greet_user called for {name}, authenticated.")
    return {"message": f"Hello, {name}! Your token was verified."}


# ADD MCP setup AFTER endpoints
# Configure for better schema descriptions
mcp = FastApiMCP(
    app,
    describe_all_responses=True,
    describe_full_response_schema=True
)
mcp.mount()
