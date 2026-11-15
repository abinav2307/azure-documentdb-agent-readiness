# Known accelerators for Azure DocumentDB builds

Edit this list as the tooling changes. The readiness checker compares it with what is installed.

| Accelerator | What it gives an agent | Where it lives | How to add it |
|---|---|---|---|
| Azure DocumentDB MCP Toolkit | Data-plane tools: query, aggregate, index management, schema inspection | github.com/microsoft/documentdb-mcp | Entry `documentdb` in `mcp.json` |
| DocumentDB Agent Kit | Agent skills with design guidance: data modeling, indexing, vector search, connection, security, deployment, driver | github.com/Azure/documentdb-agent-kit | `npx skills add Azure/documentdb-agent-kit` |
| Azure MCP Server | Control-plane tools across Azure, Azure CLI passthrough, best-practice lookups | github.com/microsoft/mcp | Entry `azure` in `mcp.json` |
| Microsoft Learn MCP Server | Search and fetch of official documentation | learn.microsoft.com/api/mcp | Entry `learn` in `mcp.json` |
| Azure CLI | Provision and inspect clusters | learn.microsoft.com/cli/azure | Install, then `az login` |
| Local DocumentDB container | Run the open-source engine locally for tests | github.com/documentdb/documentdb | Docker |
