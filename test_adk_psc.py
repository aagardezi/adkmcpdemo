import asyncio
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

mcp_toolset = McpToolset(
    name="TimeMCP",
    connection_params=SseConnectionParams(
        url="http://10.0.0.2:8000/sse"
    )
)

async def test():
    try:
        session = await mcp_toolset._mcp_session_manager.create_session()
        print("Successfully created session!")
    except Exception as e:
        print(f"Failed: {type(e).__name__} - {e}")

asyncio.run(test())
