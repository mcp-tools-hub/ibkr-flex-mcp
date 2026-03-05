"""IBKR Flex Web Service MCP Server — read-only portfolio data."""

import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ibkr-portfolio")

FLEX_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"

# Cache: (xml_string, timestamp)
_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL = 60  # seconds


def _load_config() -> tuple[str, str]:
    """Load token and query ID from ~/.ibkr_flex_env or environment variables."""
    token, query_id = "", ""
    env_file = Path.home() / ".ibkr_flex_env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "IBKR_FLEX_TOKEN":
                token = v.strip()
            elif k.strip() == "IBKR_FLEX_QUERY_ID":
                query_id = v.strip()
    token = token or os.environ.get("IBKR_FLEX_TOKEN", "")
    query_id = query_id or os.environ.get("IBKR_FLEX_QUERY_ID", "")
    if not token:
        raise ValueError("IBKR_FLEX_TOKEN not found in ~/.ibkr_flex_env or env vars")
    if not query_id:
        raise ValueError("IBKR_FLEX_QUERY_ID not found in ~/.ibkr_flex_env or env vars")
    return token, query_id


def _fetch_flex(token: str, query_id: str) -> str:
    """Two-step Flex Web Service: request reference code, then poll for XML."""
    url = f"{FLEX_URL}/SendRequest?t={token}&q={query_id}&v=3"
    resp = urlopen(url, timeout=30).read().decode()
    root = ET.fromstring(resp)
    if root.findtext("Status") != "Success":
        raise RuntimeError(f"Flex request failed: {root.findtext('ErrorMessage', 'Unknown')}")

    ref = root.findtext("ReferenceCode")
    for _ in range(10):
        time.sleep(2)
        data = urlopen(f"{FLEX_URL}/GetStatement?q={ref}&t={token}&v=3", timeout=30).read().decode()
        if "<FlexStatement" in data:
            return data
        try:
            if ET.fromstring(data).findtext("ErrorCode") == "1019":
                continue
        except ET.ParseError:
            pass
    raise RuntimeError("Flex report not ready after 20s")


def _get_xml() -> str:
    """Fetch XML with caching to avoid redundant API calls."""
    now = time.time()
    if "report" in _cache:
        xml, ts = _cache["report"]
        if now - ts < CACHE_TTL:
            return xml
    token, query_id = _load_config()
    xml = _fetch_flex(token, query_id)
    _cache["report"] = (xml, now)
    return xml


@mcp.tool()
def get_portfolio() -> str:
    """Fetch current IBKR portfolio: positions, P&L, allocation, and cash balances."""
    try:
        xml = _get_xml()
    except Exception as e:
        return f"Error fetching portfolio: {e}"

    root = ET.fromstring(xml)
    lines = ["# IBKR Portfolio Snapshot\n", "## Positions"]
    lines.append(f"{'Symbol':<8} {'Qty':>10} {'Price':>10} {'Value':>12} {'AvgCost':>10} {'P&L':>10} {'%NAV':>6} {'Ccy':<4}")
    lines.append("-" * 82)
    for p in root.iter("OpenPosition"):
        if p.get("levelOfDetail", "").upper() != "SUMMARY":
            continue
        lines.append(
            f"{p.get('symbol',''):<8} {p.get('position',''):>10} {p.get('markPrice',''):>10} "
            f"{p.get('positionValue',''):>12} {p.get('costBasisPrice',''):>10} "
            f"{p.get('fifoPnlUnrealized',''):>10} {p.get('percentOfNAV',''):>6} {p.get('currency',''):<4}"
        )

    lines.append("\n## Cash")
    for c in root.iter("CashReportCurrency"):
        ccy = c.get("currency", "")
        if ccy:
            lines.append(f"  {ccy}: {c.get('endingCash', '')} (settled: {c.get('endingSettledCash', '')})")
    return "\n".join(lines)


@mcp.tool()
def get_lots() -> str:
    """Fetch individual purchase lots for all positions (for tax/CGT analysis)."""
    try:
        xml = _get_xml()
    except Exception as e:
        return f"Error fetching lots: {e}"

    root = ET.fromstring(xml)
    lines = ["# Purchase Lots\n"]
    lines.append(f"{'Symbol':<8} {'Qty':>10} {'OpenPrice':>12} {'CostBasis':>12} {'OpenDate':<20}")
    lines.append("-" * 70)
    for p in root.iter("OpenPosition"):
        if p.get("levelOfDetail", "").upper() != "LOT":
            continue
        lines.append(
            f"{p.get('symbol',''):<8} {p.get('position',''):>10} {p.get('openPrice',''):>12} "
            f"{p.get('costBasisPrice',''):>12} {p.get('openDateTime',''):<20}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_cash() -> str:
    """Fetch cash balances, deposits, withdrawals, commissions, and dividends."""
    try:
        xml = _get_xml()
    except Exception as e:
        return f"Error fetching cash: {e}"

    root = ET.fromstring(xml)
    lines = ["# Cash Report\n"]
    for c in root.iter("CashReportCurrency"):
        ccy = c.get("currency", "")
        if not ccy:
            continue
        lines.extend([
            f"**{ccy}**",
            f"  Ending Cash: {c.get('endingCash', '')}",
            f"  Settled: {c.get('endingSettledCash', '')}",
            f"  Deposits: {c.get('deposits', '')}",
            f"  Withdrawals: {c.get('withdrawals', '')}",
            f"  Commissions: {c.get('commissions', '')}",
            f"  Dividends: {c.get('dividends', '')}", "",
        ])
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
