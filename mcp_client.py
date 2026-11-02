import asyncio
import sys
import os
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def run_mcp_client(sender, subject, snippet):
    """
    Connects to the local MCP server via stdio and calls the append_to_sheet tool.
    """
    server_path = sys.executable
    server_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    
    server_params = StdioServerParameters(
        command=server_path,
        args=[server_script]
    )

    async with AsyncExitStack() as stack:
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio_transport
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        await session.initialize()
        
        result = await session.call_tool(
            "append_to_sheet",
            arguments={
                "sender": sender,
                "subject": subject,
                "snippet": snippet
            }
        )
        return result.content[0].text if result.content else "No result"

def append_to_google_sheet(sender, subject, snippet):
    """
    Synchronous wrapper for the async MCP client call.
    """
    return asyncio.run(run_mcp_client(sender, subject, snippet))

if __name__ == "__main__":
    res = append_to_google_sheet("test@example.com", "Test Subject", "Test Snippet")
    print("MCP Server Response:", res)
