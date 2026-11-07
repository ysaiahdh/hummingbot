import asyncio
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from hummingbot.connector.exchange.safetrade import safetrade_constants as CONSTANTS
from hummingbot.connector.exchange.safetrade.safetrade_auth import SafetradeAuth
from hummingbot.connector.exchange.safetrade.safetrade_web_utils import build_api_factory
from hummingbot.connector.exchange_py_base import ExchangePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.trade_fee import AddedToCostTradeFee, TokenAmount, TradeFeeBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest

class SafetradeExchange(ExchangePyBase):
    def __init__(
        self,
        client_config_map: "ClientConfigMap",
        safetrade_api_key: str,
        safetrade_api_secret: str,
        trading_pairs: Optional[List[str]] = None,
        trading_required: bool = True,
        domain: str = CONSTANTS.DEFAULT_DOMAIN,
    ):
        self.api_key = safetrade_api_key
        self.secret_key = safetrade_api_secret
        self._domain = domain
        super().__init__(client_config_map)
        self._trading_required = trading_required
        self._trading_pairs = trading_pairs or []

    @property
    def name(self) -> str:
        return "safetrade"

    @property
    def authenticator(self) -> SafetradeAuth:
        return SafetradeAuth(self.api_key, self.secret_key)

    @property
    def rate_limits_rules(self):
        return CONSTANTS.RATE_LIMITS

    @property
    def domain(self):
        return self._domain

    @property
    def client_order_id_max_length(self):
        return 32

    @property
    def client_order_id_prefix(self):
        return "HBOT"

    @property
    def trading_rules_request_path(self):
        return CONSTANTS.EXCHANGE_INFO_PATH_URL

    @property
    def check_network_request_path(self):
        return CONSTANTS.CHECK_NETWORK_PATH_URL

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        return True

    @property
    def is_trading_required(self) -> bool:
        return self._trading_required

    def supported_order_types(self):
        return [OrderType.LIMIT, OrderType.MARKET]

    def _create_web_assistants_factory(self):
        return build_api_factory(throttler=self._throttler, auth=self.authenticator)

    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception):
        return False

    def _is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        return "order.not_found" in str(status_update_exception).lower()

    def _is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        return "order.not_found" in str(cancelation_exception).lower()

    async def _place_order(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        trade_type: TradeType,
        order_type: OrderType,
        price: Decimal,
        **kwargs,
    ) -> Tuple[str, float]:
        market = trading_pair.replace("-", "").lower()
        side = "buy" if trade_type == TradeType.BUY else "sell"
        ord_type = "limit" if order_type == OrderType.LIMIT else "market"

        payload = {
            "market": market,
            "side": side,
            "volume": str(amount),
            "ord_type": ord_type,
        }
        if order_type == OrderType.LIMIT:
            payload["price"] = str(price)

        rest_assistant = await self._web_assistants_factory.get_rest_assistant()
        url = f"{CONSTANTS.REST_URL}{CONSTANTS.ORDER_CREATE_PATH_URL}"
        req = RESTRequest(
            method=RESTMethod.POST,
            url=url,
            data=payload,
            is_auth_required=True,
            throttler_limit_id=CONSTANTS.ORDER_CREATE_PATH_URL,
        )
        response = await rest_assistant.call(req)
        data = await response.json()
        exchange_order_id = str(data["id"])
        transact_time = float(time.time())

        return exchange_order_id, transact_time

    async def _execute_order_cancel(self, order: InFlightOrder) -> bool:
        rest_assistant = await self._web_assistants_factory.get_rest_assistant()
        url = f"{CONSTANTS.REST_URL}{CONSTANTS.ORDER_CANCEL_PATH_URL}"
        payload = {"id": order.exchange_order_id}
        req = RESTRequest(
            method=RESTMethod.POST,
            url=url,
            data=payload,
            is_auth_required=True,
            throttler_limit_id=CONSTANTS.ORDER_CANCEL_PATH_URL,
        )
        response = await rest_assistant.call(req)
        if response.status == 200:
            return True
        return False

    async def _update_balances(self):
        rest_assistant = await self._web_assistants_factory.get_rest_assistant()
        url = f"{CONSTANTS.REST_URL}{CONSTANTS.USER_BALANCES_PATH_URL}"
        req = RESTRequest(
            method=RESTMethod.GET,
            url=url,
            is_auth_required=True,
            throttler_limit_id=CONSTANTS.USER_BALANCES_PATH_URL,
        )
        response = await rest_assistant.call(req)
        data = await response.json()

        self._account_available_balances.clear()
        self._account_balances.clear()

        for balance_entry in data:
            asset = balance_entry.get("currency", "").upper()
            free_balance = Decimal(str(balance_entry.get("balance", "0")))
            locked_balance = Decimal(str(balance_entry.get("locked", "0")))
            total_balance = free_balance + locked_balance

            self._account_available_balances[asset] = free_balance
            self._account_balances[asset] = total_balance

    async def _format_trading_rules(self, raw_trading_pair_info: List[Dict[str, Any]]) -> List[TradingRule]:
        trading_rules = []
        for info in raw_trading_pair_info:
            try:
                base_asset = info["base_unit"].upper()
                quote_asset = info["quote_unit"].upper()
                trading_pair = f"{base_asset}-{quote_asset}"

                min_amount = Decimal(str(info.get("min_amount", "0.0001")))
                min_price_increment = Decimal(f"1e-{info.get('price_precision', 6)}")
                min_base_amount_increment = Decimal(f"1e-{info.get('amount_precision', 4)}")

                trading_rules.append(
                    TradingRule(
                        trading_pair=trading_pair,
                        min_order_size=min_amount,
                        min_price_increment=min_price_increment,
                        min_base_amount_increment=min_base_amount_increment,
                    )
                )
            except Exception:
                continue
        return trading_rules

    async def _update_trading_fees(self):
        pass

    async def _user_stream_event_listener(self):
        while True:
            await asyncio.sleep(60)

    async def _all_trade_updates_for_order(self, order: InFlightOrder) -> List[TradeUpdate]:
        return []

    async def _request_order_status(self, track_order: InFlightOrder) -> OrderUpdate:
        rest_assistant = await self._web_assistants_factory.get_rest_assistant()
        path = CONSTANTS.ORDER_STATUS_PATH_URL.format(id=track_order.exchange_order_id)
        url = f"{CONSTANTS.REST_URL}{path}"
        req = RESTRequest(
            method=RESTMethod.GET,
            url=url,
            is_auth_required=True,
            throttler_limit_id=CONSTANTS.ORDER_STATUS_PATH_URL,
        )
        response = await rest_assistant.call(req)
        data = await response.json()

        state_map = {
            "wait": OrderState.OPEN,
            "done": OrderState.FILLED,
            "cancel": OrderState.CANCELED,
            "reject": OrderState.FAILED,
        }
        order_update = OrderUpdate(
            trading_pair=track_order.trading_pair,
            update_timestamp=float(time.time()),
            new_state=state_map.get(data.get("state", "wait"), OrderState.OPEN),
            client_order_id=track_order.client_order_id,
            exchange_order_id=str(data.get("id")),
        )
        return order_update

    async def get_last_traded_prices(self, trading_pairs: List[str], domain: Optional[str] = None) -> Dict[str, float]:
        results = {}
        rest_assistant = await self._web_assistants_factory.get_rest_assistant()
        for pair in trading_pairs:
            market = pair.replace("-", "").lower()
            path = CONSTANTS.TICKER_PATH_URL.format(market=market)
            url = f"{CONSTANTS.REST_URL}{path}"
            req = RESTRequest(
                method=RESTMethod.GET,
                url=url,
                throttler_limit_id=CONSTANTS.TICKER_PATH_URL,
            )
            response = await rest_assistant.call(req)
            data = await response.json()
            results[pair] = float(data.get("ticker", {}).get("last", 0.0))
        return results

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        market = trading_pair.replace("-", "").lower()
        rest_assistant = await self._web_assistants_factory.get_rest_assistant()
        path = CONSTANTS.SNAPSHOT_PATH_URL.format(market=market)
        url = f"{CONSTANTS.REST_URL}{path}"
        req = RESTRequest(
            method=RESTMethod.GET,
            url=url,
            throttler_limit_id=CONSTANTS.SNAPSHOT_PATH_URL,
        )
        response = await rest_assistant.call(req)
        data = await response.json()

        timestamp = time.time()
        return OrderBookMessage(
            OrderBookMessageType.SNAPSHOT,
            {
                "trading_pair": trading_pair,
                "update_id": int(timestamp * 1000),
                "bids": [[Decimal(p), Decimal(v)] for p, v in data.get("bids", [])],
                "asks": [[Decimal(p), Decimal(v)] for p, v in data.get("asks", [])],
            },
            timestamp=timestamp,
        )