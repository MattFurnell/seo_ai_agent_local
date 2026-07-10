import os

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY")
SEMRUSH_MCP_URL = os.getenv(
    "SEMRUSH_MCP_URL",
    "https://mcp.semrush.com/v1/mcp",
)


async def ask_semrush(question: str) -> str:
    """Use Gemini with the live Semrush MCP tools and return the final answer."""
    if not GEMINI_API_KEY:
        return "Gemini is not configured. Add GEMINI_API_KEY to the .env file."

    if not SEMRUSH_API_KEY:
        return "Semrush is not configured. Add SEMRUSH_API_KEY to the .env file."

    headers = {
        "Authorization": f"Apikey {SEMRUSH_API_KEY}"
    }

    prompt = f"""
You are an SEO Intelligence Agent for Howden C&LC.

Use the available Semrush MCP tools whenever live Semrush data is needed.

Rules:
- Use live Semrush tool data, not general knowledge, for factual Semrush results.
- Do not simulate API calls.
- Do not invent metrics.
- If a report requires a schema first, call get_report_schema before execute_report.
- Clearly state when Semrush does not return a requested metric.
- Explain the final result in clear, practical English.

User question:
{question}
"""

    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        async with streamablehttp_client(
            SEMRUSH_MCP_URL,
            headers=headers,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                response = await gemini_client.aio.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config={"tools": [session]},
                )

                return response.text or "Gemini returned an empty response."

    except Exception as error:
        return f"The live Semrush MCP request failed. Error detail: {error}"