"""Data models for IBKR Flex Web Service XML responses."""

from pydantic_xml import BaseXmlModel, attr


class Position(BaseXmlModel, tag="OpenPosition"):
    symbol: str = attr()
    description: str = attr(default="")
    currency: str = attr(default="")
    asset_class: str = attr(name="assetCategory", default="")
    exchange: str = attr(name="listingExchange", default="")
    quantity: str = attr(name="position", default="")
    mark_price: str = attr(name="markPrice", default="")
    position_value: str = attr(name="positionValue", default="")
    cost_basis_price: str = attr(name="costBasisPrice", default="")
    cost_basis_money: str = attr(name="costBasisMoney", default="")
    unrealized_pnl: str = attr(name="fifoPnlUnrealized", default="")
    pct_of_nav: str = attr(name="percentOfNAV", default="")
    open_price: str = attr(name="openPrice", default="")
    fx_rate: str = attr(name="fxRateToBase", default="")
    side: str = attr(default="")
    level_of_detail: str = attr(name="levelOfDetail", default="")
    open_date: str = attr(name="openDateTime", default="")
    holding_period: str = attr(name="holdingPeriodDateTime", default="")

    @property
    def is_summary(self) -> bool:
        return self.level_of_detail.upper() == "SUMMARY"

    @property
    def is_lot(self) -> bool:
        return self.level_of_detail.upper() == "LOT"


class CashBalance(BaseXmlModel, tag="CashReportCurrency"):
    currency: str = attr(default="")
    ending_cash: str = attr(name="endingCash", default="")
    ending_settled: str = attr(name="endingSettledCash", default="")
    deposits: str = attr(default="")
    withdrawals: str = attr(default="")
    commissions: str = attr(default="")
    dividends: str = attr(default="")
