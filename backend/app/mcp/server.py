"""
Bijmantra MCP Server
Model Context Protocol server for AI model integration

This allows AI assistants (Claude, GPT, etc.) to:
- Query germplasm database
- Search breeding trials
- Get phenotype observations
- Access breeding protocols
- Perform semantic search

Usage:
    uvx bijmantra-mcp-server
    
Or run directly:
    python -m app.mcp.server
"""

import json
import asyncio
from typing import Any, Optional, List, Dict
from datetime import datetime

# MCP SDK imports (fastmcp)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        ResourceTemplate,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[MCP] mcp package not installed. Install with: pip install mcp")

# Internal imports for database access
import httpx


# ============================================
# CONFIGURATION
# ============================================

BIJMANTRA_API_URL = "http://localhost:8000"
MCP_SERVER_NAME = "bijmantra"
MCP_SERVER_VERSION = "1.0.0"  # Synced with metrics.json


# ============================================
# API CLIENT
# ============================================

class BijmantraClient:
    """HTTP client for Bijmantra API"""
    
    def __init__(self, base_url: str = BIJMANTRA_API_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Bijmantra API"""
        async with httpx.AsyncClient() as client:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response.json()
    
    async def get_programs(self, page: int = 0, page_size: int = 20) -> Dict:
        """Get breeding programs"""
        return await self._request(
            "GET", 
            "/brapi/v2/programs",
            params={"page": page, "pageSize": page_size}
        )
    
    async def get_program(self, program_id: str) -> Dict:
        """Get a specific program"""
        return await self._request("GET", f"/brapi/v2/programs/{program_id}")
    
    async def get_trials(self, page: int = 0, page_size: int = 20) -> Dict:
        """Get trials"""
        return await self._request(
            "GET",
            "/brapi/v2/trials",
            params={"page": page, "pageSize": page_size}
        )
    
    async def get_trial(self, trial_id: str) -> Dict:
        """Get a specific trial"""
        return await self._request("GET", f"/brapi/v2/trials/{trial_id}")
    
    async def get_studies(self, page: int = 0, page_size: int = 20) -> Dict:
        """Get studies"""
        return await self._request(
            "GET",
            "/brapi/v2/studies",
            params={"page": page, "pageSize": page_size}
        )
    
    async def get_germplasm(self, page: int = 0, page_size: int = 20) -> Dict:
        """Get germplasm entries"""
        return await self._request(
            "GET",
            "/brapi/v2/germplasm",
            params={"page": page, "pageSize": page_size}
        )
    
    async def search_germplasm(self, query: str) -> Dict:
        """Search germplasm by name or attributes"""
        return await self._request(
            "GET",
            "/brapi/v2/germplasm",
            params={"germplasmName": query}
        )
    
    async def get_locations(self, page: int = 0, page_size: int = 20) -> Dict:
        """Get locations"""
        return await self._request(
            "GET",
            "/brapi/v2/locations",
            params={"page": page, "pageSize": page_size}
        )
    
    async def semantic_search(self, query: str, limit: int = 10) -> Dict:
        """Perform semantic search across breeding data"""
        return await self._request(
            "POST",
            "/api/v2/vector/search",
            data={"query": query, "limit": limit}
        )
    
    async def chat_with_veena(self, message: str) -> Dict:
        """Chat with Veena AI assistant"""
        return await self._request(
            "POST",
            "/api/v2/chat",
            data={"message": message, "include_context": True}
        )
    
    async def get_server_info(self) -> Dict:
        """Get BrAPI server info"""
        return await self._request("GET", "/brapi/v2/serverinfo")


# ============================================
# MCP SERVER
# ============================================

if MCP_AVAILABLE:
    # Create MCP server
    server = Server(MCP_SERVER_NAME)
    client = BijmantraClient()
    
    # ----------------------------------------
    # TOOLS
    # ----------------------------------------
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools"""
        return [
            Tool(
                name="list_programs",
                description="List all breeding programs in Bijmantra",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "default": 0},
                        "pageSize": {"type": "integer", "default": 20}
                    }
                }
            ),
            Tool(
                name="get_program",
                description="Get details of a specific breeding program",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "programId": {"type": "string", "description": "The program ID"}
                    },
                    "required": ["programId"]
                }
            ),
            Tool(
                name="list_trials",
                description="List all breeding trials",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "default": 0},
                        "pageSize": {"type": "integer", "default": 20}
                    }
                }
            ),
            Tool(
                name="get_trial",
                description="Get details of a specific trial",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trialId": {"type": "string", "description": "The trial ID"}
                    },
                    "required": ["trialId"]
                }
            ),
            Tool(
                name="list_germplasm",
                description="List germplasm entries (plant genetic resources)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "default": 0},
                        "pageSize": {"type": "integer", "default": 20}
                    }
                }
            ),
            Tool(
                name="search_germplasm",
                description="Search for germplasm by name or characteristics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="list_locations",
                description="List all research locations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "default": 0},
                        "pageSize": {"type": "integer", "default": 20}
                    }
                }
            ),
            Tool(
                name="semantic_search",
                description="Perform semantic search across all breeding data using AI embeddings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language search query"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="ask_veena",
                description="Ask Veena, the AI breeding assistant, a question about plant breeding",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "Your question for Veena"}
                    },
                    "required": ["question"]
                }
            ),
            Tool(
                name="server_info",
                description="Get information about the Bijmantra BrAPI server",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a tool"""
        try:
            if name == "list_programs":
                result = await client.get_programs(
                    page=arguments.get("page", 0),
                    page_size=arguments.get("pageSize", 20)
                )
            elif name == "get_program":
                result = await client.get_program(arguments["programId"])
            elif name == "list_trials":
                result = await client.get_trials(
                    page=arguments.get("page", 0),
                    page_size=arguments.get("pageSize", 20)
                )
            elif name == "get_trial":
                result = await client.get_trial(arguments["trialId"])
            elif name == "list_germplasm":
                result = await client.get_germplasm(
                    page=arguments.get("page", 0),
                    page_size=arguments.get("pageSize", 20)
                )
            elif name == "search_germplasm":
                result = await client.search_germplasm(arguments["query"])
            elif name == "list_locations":
                result = await client.get_locations(
                    page=arguments.get("page", 0),
                    page_size=arguments.get("pageSize", 20)
                )
            elif name == "semantic_search":
                result = await client.semantic_search(
                    query=arguments["query"],
                    limit=arguments.get("limit", 10)
                )
            elif name == "ask_veena":
                result = await client.chat_with_veena(arguments["question"])
            elif name == "server_info":
                result = await client.get_server_info()
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    # ----------------------------------------
    # RESOURCES
    # ----------------------------------------
    
    @server.list_resources()
    async def list_resources() -> List[Resource]:
        """List available resources"""
        return [
            Resource(
                uri="bijmantra://programs",
                name="Breeding Programs",
                description="All breeding programs in the system",
                mimeType="application/json"
            ),
            Resource(
                uri="bijmantra://trials",
                name="Breeding Trials",
                description="All breeding trials",
                mimeType="application/json"
            ),
            Resource(
                uri="bijmantra://germplasm",
                name="Germplasm Collection",
                description="Plant genetic resources",
                mimeType="application/json"
            ),
            Resource(
                uri="bijmantra://locations",
                name="Research Locations",
                description="Field trial and research locations",
                mimeType="application/json"
            ),
        ]
    
    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a resource"""
        try:
            if uri == "bijmantra://programs":
                result = await client.get_programs()
            elif uri == "bijmantra://trials":
                result = await client.get_trials()
            elif uri == "bijmantra://germplasm":
                result = await client.get_germplasm()
            elif uri == "bijmantra://locations":
                result = await client.get_locations()
            else:
                return json.dumps({"error": f"Unknown resource: {uri}"})
            
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # ----------------------------------------
    # RESOURCE TEMPLATES
    # ----------------------------------------
    
    @server.list_resource_templates()
    async def list_resource_templates() -> List[ResourceTemplate]:
        """List resource templates"""
        return [
            ResourceTemplate(
                uriTemplate="bijmantra://programs/{programId}",
                name="Breeding Program",
                description="Get a specific breeding program by ID"
            ),
            ResourceTemplate(
                uriTemplate="bijmantra://trials/{trialId}",
                name="Breeding Trial",
                description="Get a specific trial by ID"
            ),
        ]
    
    # ----------------------------------------
    # MAIN
    # ----------------------------------------
    
    async def main():
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )


def run_server():
    """Entry point for running the MCP server"""
    if not MCP_AVAILABLE:
        print("Error: MCP package not installed")
        print("Install with: pip install mcp")
        return
    
    print(f"[Bijmantra MCP] Starting server v{MCP_SERVER_VERSION}")
    print(f"[Bijmantra MCP] Connecting to API at {BIJMANTRA_API_URL}")
    asyncio.run(main())


if __name__ == "__main__":
    run_server()
