import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SCREAMING_FROG_MCP_URL = os.getenv("SCREAMING_FROG_MCP_URL")

MAX_TOOL_STEPS = 4


def extract_text(result: Any) -> str:
    parts = []
    for item in getattr(result, "content", []) or []:
        if getattr(item, "type", None) == "text":
            parts.append(item.text)
    return "\n".join(parts)


def clean_json_response(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def serialise_tools(tools: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        }
        for tool in tools
    ]


async def choose_next_action(
    gemini_client: genai.Client,
    question: str,
    tools: list[dict[str, Any]],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt = f"""
You are controlling Screaming Frog SEO Spider through its MCP tools.

User request:
{question}

Available Screaming Frog tools:
{json.dumps(tools, indent=2)}

Previous tool calls and results:
{json.dumps(history, indent=2)}

Choose the next action.

Rules:
- Base your choice only on the supplied tool names, descriptions and schemas.
- Never invent a tool or argument.
- Prefer read-only tools when an existing saved crawl can answer the question.
- Use sf_list_crawls first when you need to identify an existing crawl.
- Use the exact instanceDirName returned by sf_list_crawls when another tool needs a crawl identifier.
- Start a new crawl only when the user explicitly asks for one and a suitable saved crawl is not enough.
- Return valid JSON only. Do not use Markdown.
- To call a tool, return:
  {{"action":"call_tool","tool_name":"exact_name","arguments":{{...}}}}
- When enough live data has been collected, return:
  {{"action":"finish","reason":"brief explanation"}}
"""

    response = await gemini_client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    raw_text = response.text or ""
    return json.loads(clean_json_response(raw_text))


async def summarise_results(
    gemini_client: genai.Client,
    question: str,
    history: list[dict[str, Any]],
) -> str:
    prompt = f"""
You are an SEO Intelligence Agent for Howden C&LC.

User request:
{question}

Live Screaming Frog MCP tool calls and results:
{json.dumps(history, indent=2)}

Write the final answer.

Rules:
- Use only the live tool results above for factual crawl findings.
- Do not simulate a crawl.
- Do not invent URLs, counts or issues.
- Say clearly when the available result does not contain a requested metric.
- Keep the explanation practical and structured.
- Distinguish between an existing saved crawl and a newly run crawl.
"""

    response = await gemini_client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text or "Gemini returned an empty response."


async def ask_screaming_frog(question: str) -> str:
    if not GEMINI_API_KEY:
        return "Gemini is not configured. Add GEMINI_API_KEY to .env."

    if not SCREAMING_FROG_MCP_URL:
        return (
            "Screaming Frog MCP is not configured. "
            "Add SCREAMING_FROG_MCP_URL to .env."
        )

    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    history: list[dict[str, Any]] = []

    try:
        async with streamablehttp_client(
            SCREAMING_FROG_MCP_URL
        ) as (read_stream, write_stream, _):

            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:

                await session.initialize()
                tools_result = await session.list_tools()
                tools = serialise_tools(tools_result.tools)
                valid_tool_names = {tool["name"] for tool in tools}

                for _ in range(MAX_TOOL_STEPS):
                    decision = await choose_next_action(
                        gemini_client=gemini_client,
                        question=question,
                        tools=tools,
                        history=history,
                    )

                    action = decision.get("action")

                    if action == "finish":
                        break

                    if action != "call_tool":
                        raise ValueError(
                            f"Unexpected Gemini action: {decision}"
                        )

                    tool_name = decision.get("tool_name")
                    arguments = decision.get("arguments", {})

                    if tool_name not in valid_tool_names:
                        raise ValueError(
                            f"Gemini selected an unknown tool: {tool_name}"
                        )

                    if not isinstance(arguments, dict):
                        raise ValueError(
                            "Gemini returned invalid tool arguments."
                        )

                    result = await session.call_tool(
                        tool_name,
                        arguments=arguments,
                    )

                    result_text = extract_text(result)

                    history.append(
                        {
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "is_error": bool(
                                getattr(result, "isError", False)
                            ),
                            "result": result_text,
                        }
                    )

                    if getattr(result, "isError", False):
                        continue

                if not history:
                    return (
                        "Screaming Frog MCP connected, but no tool call "
                        "was selected for this request."
                    )

                return await summarise_results(
                    gemini_client=gemini_client,
                    question=question,
                    history=history,
                )

    except BaseException as error:
        return (
            "The live Screaming Frog MCP request failed. "
            f"Error detail: {type(error).__name__}: {error}"
        )
