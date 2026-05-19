# MCP Context7 Configuration

To ensure your AI coding assistants (like Cursor, Claude Code, etc.) have access to the most up-to-date documentation and code patterns, we are using the **Context7** MCP server.

## Installation

### For Cursor
1. Open Cursor Settings -> Features -> MCP Servers
2. Click "Add New MCP Server"
3. Set the name to `context7`
4. Set the type to `command`
5. Set the command to: `npx -y @upstash/context7-mcp`

### For Claude Desktop
Add the following to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

## Usage
The `.cursorrules` file in this repository already instructs the AI to use `context7` for fetching documentation. When asking the AI for help with library updates (like our Angular migration) or framework usage, it will automatically retrieve the correct version context.
