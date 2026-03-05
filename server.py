"""IBKR Flex Web Service MCP Server — read-only portfolio data."""

from mcp.server.fastmcp import FastMCP

from client import FlexClient

mcp = FastMCP("ibkr-portfolio")
client = FlexClient()


@mcp.tool()
def get_portfolio() -> str:
    """Fetch current IBKR portfolio: positions, P&L, allocation, and cash balances."""
    try:
        report = client.get_report()
    except Exception as e:
        return f"Error fetching portfolio: {e}"

    lines = ["# IBKR Portfolio Snapshot\n", "## Positions"]
    lines.append(f"{'Symbol':<8} {'Qty':>10} {'Price':>10} {'Value':>12} {'AvgCost':>10} {'P&L':>10} {'%NAV':>6} {'Ccy':<4}")
    lines.append("-" * 82)
    for p in report.positions:
        lines.append(
            f"{p.symbol:<8} {p.quantity:>10} {p.mark_price:>10} "
            f"{p.position_value:>12} {p.cost_basis_price:>10} "
            f"{p.unrealized_pnl:>10} {p.pct_of_nav:>6} {p.currency:<4}"
        )
    lines.append("\n## Cash")
    for c in report.cash:
        lines.append(f"  {c.currency}: {c.ending_cash} (settled: {c.ending_settled})")
    return "\n".join(lines)


@mcp.tool()
def get_lots() -> str:
    """Fetch individual purchase lots for all positions (for tax/CGT analysis)."""
    try:
        report = client.get_report()
    except Exception as e:
        return f"Error fetching lots: {e}"

    lines = ["# Purchase Lots\n"]
    lines.append(f"{'Symbol':<8} {'Qty':>10} {'OpenPrice':>12} {'CostBasis':>12} {'OpenDate':<20}")
    lines.append("-" * 70)
    for lot in report.lots:
        lines.append(
            f"{lot.symbol:<8} {lot.quantity:>10} {lot.open_price:>12} "
            f"{lot.cost_basis_price:>12} {lot.open_date:<20}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_cash() -> str:
    """Fetch cash balances, deposits, withdrawals, commissions, and dividends."""
    try:
        report = client.get_report()
    except Exception as e:
        return f"Error fetching cash: {e}"

    lines = ["# Cash Report\n"]
    for c in report.cash:
        lines.extend([
            f"**{c.currency}**",
            f"  Ending Cash: {c.ending_cash}",
            f"  Settled: {c.ending_settled}",
            f"  Deposits: {c.deposits}",
            f"  Withdrawals: {c.withdrawals}",
            f"  Commissions: {c.commissions}",
            f"  Dividends: {c.dividends}", "",
        ])
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
