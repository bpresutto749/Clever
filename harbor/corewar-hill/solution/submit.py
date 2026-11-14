import asyncio, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main(path, url="http://arena:8000/mcp"):
    src = open(path).read()
    async with streamablehttp_client(url) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("submit", {"source": src})
            print(res.content[0].text)

asyncio.run(main(*sys.argv[1:]))
