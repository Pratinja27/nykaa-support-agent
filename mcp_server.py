from fastmcp import FastMCP
from tools.order_tool import check_order_status

# Initialize FastMCP Server
mcp = FastMCP("Nykaa Order Tools")


@mcp.tool()
def fetch_order_status(record_id: str) -> dict:
    """Retrieves order status, amount, and escalation metrics from Nykaa database."""
    return check_order_status(record_id)


if __name__ == "__main__":
    mcp.run(transport="http", port=8001)