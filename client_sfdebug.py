import asyncio
import json
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

SCREAMING_FROG_MCP_URL = os.getenv("SCREAMING_FROG_MCP_URL")


def extract_text(result) -> str:
    parts = []
    for item in getattr(result, "content", []) or []:
        if getattr(item, "type", None) == "text":
            parts.append(item.text)
    return "\n".join(parts)


async def main():
    if not SCREAMING_FROG_MCP_URL:
        print("ERROR: SCREAMING_FROG_MCP_URL is missing from .env")
        return

    print("Connecting to:", SCREAMING_FROG_MCP_URL)

    async with streamablehttp_client(
        SCREAMING_FROG_MCP_URL
    ) as (read_stream, write_stream, _):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()
            tools_result = await session.list_tools()

            print("\n✅ Connected to Screaming Frog MCP")
            print("\nAvailable tools and schemas:\n")

            tools_by_name = {}

            for tool in tools_result.tools:
                tools_by_name[tool.name] = tool
                print("=" * 80)
                print("TOOL:", tool.name)
                print("DESCRIPTION:", tool.description or "")
                print("INPUT SCHEMA:")
                print(json.dumps(tool.inputSchema, indent=2))
                print()

            tool_name = input(
                "\nEnter a tool name exactly as shown, or press Enter to finish: "
            ).strip()

            if not tool_name:
                return

            if tool_name not in tools_by_name:
                print(f"Unknown tool: {tool_name}")
                return

            raw_arguments = input(
                'Enter arguments as JSON, or press Enter for {}: '
            ).strip()

            try:
                arguments = json.loads(raw_arguments) if raw_arguments else {}
            except json.JSONDecodeError as error:
                print(f"Invalid JSON: {error}")
                return

            print(f"\nCalling {tool_name} with:")
            print(json.dumps(arguments, indent=2))

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            print("\nRAW MCP RESULT:")
            print(result)

            print("\nCLEAN TEXT RESULT:")
            text = extract_text(result)

            if not text:
                print("(No text content returned.)")
                return

            try:
                parsed = json.loads(text)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print(text)

            print("\nisError:", getattr(result, "isError", None))


if __name__ == "__main__":
    asyncio.run(main())
