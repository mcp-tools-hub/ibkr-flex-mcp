"""IBKR Flex Web Service API client with caching."""

import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import urlopen

from models import CashBalance, Position

FLEX_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
CACHE_TTL = 60


@dataclass
class FlexReport:
    """Parsed Flex Query result."""
    positions: list[Position] = field(default_factory=list)
    lots: list[Position] = field(default_factory=list)
    cash: list[CashBalance] = field(default_factory=list)


class FlexClient:
    """Fetches and parses IBKR Flex Web Service reports."""

    def __init__(self) -> None:
        self._cache: tuple[FlexReport, float] | None = None
        self._token, self._query_id = self._load_config()

    @staticmethod
    def _load_config() -> tuple[str, str]:
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

    def _fetch_xml(self) -> str:
        """Two-step Flex Web Service: request reference code, then poll for XML."""
        resp = urlopen(
            f"{FLEX_URL}/SendRequest?t={self._token}&q={self._query_id}&v=3", timeout=30
        ).read().decode()
        root = ET.fromstring(resp)
        if root.findtext("Status") != "Success":
            raise RuntimeError(f"Flex request failed: {root.findtext('ErrorMessage', 'Unknown')}")

        ref = root.findtext("ReferenceCode")
        for _ in range(10):
            time.sleep(2)
            data = urlopen(
                f"{FLEX_URL}/GetStatement?q={ref}&t={self._token}&v=3", timeout=30
            ).read().decode()
            if "<FlexStatement" in data:
                return data
            try:
                if ET.fromstring(data).findtext("ErrorCode") == "1019":
                    continue
            except ET.ParseError:
                pass
        raise RuntimeError("Flex report not ready after 20s")

    @staticmethod
    def _parse(xml: str) -> FlexReport:
        root = ET.fromstring(xml)
        all_positions = [
            Position.from_xml_tree(el) for el in root.iter("OpenPosition")
        ]
        cash = [
            CashBalance.from_xml_tree(el) for el in root.iter("CashReportCurrency")
            if el.get("currency", "")
        ]
        return FlexReport(
            positions=[p for p in all_positions if p.is_summary],
            lots=[p for p in all_positions if p.is_lot],
            cash=cash,
        )

    def get_report(self) -> FlexReport:
        """Fetch report with caching."""
        now = time.time()
        if self._cache and (now - self._cache[1]) < CACHE_TTL:
            return self._cache[0]
        report = self._parse(self._fetch_xml())
        self._cache = (report, now)
        return report
