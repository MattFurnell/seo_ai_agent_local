import asyncio
import os
from dotenv import load_dotenv
from google import genai

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SEMRUSH_MCP_URL = os.getenv("SEMRUSH_MCP_URL", "https://mcp.semrush.com/v2/mcp")

client = genai.Client(api_key=GEMINI_API_KEY)


async def main():
    headers = {}

    async with streamablehttp_client(SEMRUSH_MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()

            print("\n✅ Connected to Semrush MCP")
            print("\nAvailable tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents="What Semrush tools are available to help with keyword research?",
                config={
                    "tools": [session]
                },
            )

            print("\nGemini response:")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(main())