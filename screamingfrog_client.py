import os

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SCREAMING_FROG_MCP_URL = os.getenv("SCREAMING_FROG_MCP_URL")


async def ask_screaming_frog(question: str) -> str:
    """Use Gemini with the live Screaming Frog MCP tools."""

    if not GEMINI_API_KEY:
        return "Gemini is not configured."

    if not SCREAMING_FROG_MCP_URL:
        return "Screaming Frog MCP is not configured."

    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are an SEO Intelligence Agent for Howden C&LC.

Use the available Screaming Frog MCP tools to complete the user's request.

Rules:
- Use live Screaming Frog crawl data.
- Do not simulate crawls or invent metrics.
- Ask for a website URL if one is required and has not been supplied.
- Clearly explain what crawl or report was run.
- Summarise findings in practical, plain English.

User question:
{question}
"""

    try:
        async with streamablehttp_client(
            SCREAMING_FROG_MCP_URL
        ) as (read_stream, write_stream, _):

            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:

                await session.initialize()

                response = await gemini_client.aio.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config={"tools": [session]},
                )

                return response.text or "Gemini returned an empty response."

    except Exception as error:
        return (
            "The live Screaming Frog MCP request failed. "
            f"Error detail: {error}"
        )