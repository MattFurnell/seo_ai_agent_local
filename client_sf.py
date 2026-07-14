import asyncio

from screamingfrog_client import ask_screaming_frog


async def main():
    response = await ask_screaming_frog(
        """
        Use Screaming Frog to crawl https://example.com
        and summarise any broken internal links and missing page titles.
        """
    )

    print(response)


if __name__ == "__main__":
    asyncio.run(main())