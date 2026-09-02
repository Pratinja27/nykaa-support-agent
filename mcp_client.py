import asyncio
from fastmcp import Client


async def main():
    async with Client("http://localhost:8001/mcp") as client:
        print("=== MCP CALL 1 (ORD1001) ===")
        res1 = await client.call_tool("fetch_order_status", {"record_id": "ORD1001"})
        print(res1)

        print("\n=== MCP CALL 2 (ORD1002) ===")
        res2 = await client.call_tool("fetch_order_status", {"record_id": "ORD1002"})
        print(res2)


if __name__ == "__main__":
    asyncio.run(main())