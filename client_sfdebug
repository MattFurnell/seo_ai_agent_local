import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

SCREAMING_FROG_MCP_URL = os.getenv("SCREAMING_FROG_MCP_URL")


async def main():
    print("Screaming Frog URL:", SCREAMING_FROG_MCP_URL)

    async with streamablehttp_client(
        SCREAMING_FROG_MCP_URL
    ) as (read_stream, write_stream, _):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()
            tools = await session.list_tools()

            print("\n✅ Connected to Screaming Frog MCP")
            print("\nAvailable tools:")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())
