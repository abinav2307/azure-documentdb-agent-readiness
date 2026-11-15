"""A tiny MCP server used by the tests (stdio transport)."""
from mcp.server.mcpserver import MCPServer

server = MCPServer("docs-stub")


@server.tool()
def search_docs(query: str) -> str:
    """Search the (fake) documentation."""
    return f"No documentation found for: {query}"


if __name__ == "__main__":
    server.run()
