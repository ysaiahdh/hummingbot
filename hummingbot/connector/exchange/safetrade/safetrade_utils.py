from decimal import Decimal
from pydantic import Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap, ClientFieldData
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

CENTRALIZED = True
EXAMPLE_PAIR = "PRL-USDT"

DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.002"),
    taker_percent_fee_decimal=Decimal("0.002"),
)

class SafetradeConfigMap(BaseConnectorConfigMap):
    connector: str = Field(default="safetrade", const=True, client_data=None)
    safetrade_api_key: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your SafeTrade API key",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        )
    )
    safetrade_api_secret: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your SafeTrade API secret",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        )
    )

KEYS = SafetradeConfigMap.construct()