import asyncio
import os
from dotenv import load_dotenv
from google import genai

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY") 
SEMRUSH_MCP_URL = os.getenv(    
    "SEMRUSH_MCP_URL", 
    "https://mcp.semrush.com/v1/mcp",
)

#---
# TEMPORARY DEBUG
#---
print("Semrush URL:", SEMRUSH_MCP_URL)
print("Semrush key load", bool(SEMRUSH_API_KEY))
print("Semrush key loaded", len(SEMRUSH_API_KEY) if SEMRUSH_API_KEY else 0)

client = genai.Client(api_key=GEMINI_API_KEY)


async def main():
    headers = {
        "Authorization": f"Apikey {SEMRUSH_API_KEY}"
    }

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
                contents="""Use Semrush MCP to get the top 5 organic search competitors for the keyword "young driver insurance" in the United Kingdom. Use live Semrush data, not general knowledge. Include the comepting domains and metrics returned by the tool.""",
                config={
                    "tools": [session]
                },
            )

            print("\nGemini response:")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
