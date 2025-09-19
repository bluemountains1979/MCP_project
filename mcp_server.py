from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import os
from dotenv import load_dotenv
import logging
import socket

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO", "bluemountains1979/MCP")

if not GITHUB_TOKEN:
    logger.warning("GITHUB_TOKEN not found in environment variables")
    GITHUB_TOKEN = ""

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json"
}

# Create MCP server
mcp = FastMCP("github-tools")

@mcp.tool()
def list_open_issues() -> list:
    """Return titles of open issues."""
    try:
        url = f"https://api.github.com/repos/{REPO}/issues"
        r = requests.get(url, headers=HEADERS, params={"state": "open"})
        r.raise_for_status()
        issues = r.json()
        return [{"title": issue["title"], "number": issue["number"], "url": issue["html_url"]} for issue in issues]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching issues: {e}")
        return {"error": f"Failed to fetch issues: {str(e)}"}

@mcp.tool()
def create_issue(title: str, body: str = "") -> dict:
    """Create a new issue in the repo."""
    try:
        url = f"https://api.github.com/repos/{REPO}/issues"
        data = {"title": title, "body": body}
        r = requests.post(url, headers=HEADERS, json=data)
        r.raise_for_status()
        response = r.json()
        return {
            "message": "Issue created successfully",
            "issue_number": response["number"],
            "title": response["title"],
            "url": response["html_url"]
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating issue: {e}")
        return {"error": f"Failed to create issue: {str(e)}"}

# Create FastAPI app
app = FastAPI(title="GitHub MCP Server")

# Add health endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "GitHub MCP Server"}

@app.get("/")
def root():
    return {
        "message": "GitHub MCP Server is running",
        "endpoints": {
            "health": "/health",
            "mcp_sse": "/mcp (SSE endpoint for MCP clients)"
        }
    }

# Manual JSON-RPC handler for HTTP POST requests
@app.post("/")
async def handle_json_rpc(request: Request):
    """Handle JSON-RPC requests directly"""
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})
        
        if method == "list_open_issues":
            result = list_open_issues()
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": data.get("id")
            })
        elif method == "create_issue":
            title = params.get("title", "")
            body = params.get("body", "")
            result = create_issue(title, body)
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": data.get("id")
            })
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": "Method not found"},
                "id": data.get("id")
            })
    
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": data.get("id", None)
        })

# Mount MCP SSE at a specific path for MCP clients
app.mount("/mcp", mcp.sse_app())

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    return start_port  # Fallback

if __name__ == "__main__":
    import uvicorn
    
    available_port = find_available_port()
    logger.info("Starting GitHub MCP Server...")
    logger.info(f"Using repo: {REPO}")
    logger.info(f"Server will run on port: {available_port}")
    
    uvicorn.run(app, host="0.0.0.0", port=available_port, log_level="info")