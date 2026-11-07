import asyncio
import time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from hummingbot.connector.exchange.safetrade import safetrade_constants as CONSTANTS
from hummingbot.connector.exchange.safetrade import safetrade_web_utils as web_utils
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest

if TYPE_CHECKING:
    from hummingbot.connector.exchange.safetrade.safetrade_exchange import SafetradeExchange

class SafetradeAPIOrderBookDataSource(OrderBookTrackerDataSource):
    def __init__(
        self,
        trading_pairs: List[str],
        connector: "SafetradeExchange",
        api_factory: Optional[Any] = None,
    ):
        super().__init__(trading_pairs)
        self._connector = connector
        self._api_factory = api_factory or web_utils.build_api_factory()

    async def get_last_traded_prices(self, trading_pairs: List[str], domain: Optional[str] = None) -> Dict[str, float]:
        results = {}
        rest_assistant = await self._api_factory.get_rest_assistant()
        for pair in trading_pairs:
            market = pair.replace("-", "").lower()
            url = f"{CONSTANTS.REST_URL}/api/v2/peatio/public/markets/{market}/tickers"
            req = RESTRequest(method=RESTMethod.GET, url=url)
            res = await rest_assistant.call(req)
            data = await res.json()
            results[pair] = float(data.get("ticker", {}).get("last", 0.0))
        return results

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        market = trading_pair.replace("-", "").lower()
        rest_assistant = await self._api_factory.get_rest_assistant()
        url = f"{CONSTANTS.REST_URL}/api/v2/peatio/public/markets/{market}/depth-merged"
        req = RESTRequest(method=RESTMethod.GET, url=url)
        res = await rest_assistant.call(req)
        data = await res.json()

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

    async def listen_for_subscriptions(self):
        # Maintient la boucle active pour le tracker
        while True:
            await asyncio.sleep(60)

    async def listen_for_trades(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        pass

    async def listen_for_order_book_diffs(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        pass

    async def listen_for_order_book_snapshots(self, ev_loop: asyncio.AbstractEventLoop, output: asyncio.Queue):
        while True:
            for pair in self._trading_pairs:
                try:
                    snapshot = await self._order_book_snapshot(pair)
                    output.put_nowait(snapshot)
                except Exception as e:
                    self.logger().error(f"Erreur snapshot SafeTrade pour {pair}: {e}")
                await asyncio.sleep(5)