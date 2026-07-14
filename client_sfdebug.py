import asyncio
import json
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

SCREAMING_FROG_MCP_URL = os.getenv("SCREAMING_FROG_MCP_URL")


async def main():

    print("Connecting to:", SCREAMING_FROG_MCP_URL)

    async with streamablehttp_client(
        SCREAMING_FROG_MCP_URL
    ) as (read_stream, write_stream, _):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            tools = await session.list_tools()

            print("\n✅ Connected!\n")
            print("Available tools:\n")

            for tool in tools.tools:
                print(f"- {tool.name}")

            print("\n")

            tool_name = input("Enter the tool name exactly as shown above: ")

            print("\nCalling tool...\n")

            result = await session.call_tool(
                tool_name,
                arguments={}
            )

            print("---------------")
            print("RAW RESPONSE")
            print("---------------")
            print(result)

            print("\nFinished.")


if __name__ == "__main__":
    asyncio.run(main())
