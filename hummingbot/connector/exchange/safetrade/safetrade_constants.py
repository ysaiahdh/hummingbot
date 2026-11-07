from hummingbot.core.api_throttler.data_types import RateLimit

DEFAULT_DOMAIN = "safetrade"

REST_URL = "https://safe.trade"
WSS_PUBLIC_URL = "wss://safe.trade/api/v2/ranger/public"
WSS_PRIVATE_URL = "wss://safe.trade/api/v2/ranger/private"

# Endpoints REST Peatio v2
CHECK_NETWORK_PATH_URL = "/api/v2/peatio/public/timestamp"
SERVER_TIME_PATH_URL = "/api/v2/peatio/public/timestamp"
EXCHANGE_INFO_PATH_URL = "/api/v2/peatio/public/markets"
SNAPSHOT_PATH_URL = "/api/v2/peatio/public/markets/{market}/depth-merged"
TICKER_PATH_URL = "/api/v2/peatio/public/markets/{market}/tickers"

ORDER_CREATE_PATH_URL = "/api/v2/peatio/market/orders"
ORDER_CANCEL_PATH_URL = "/api/v2/peatio/market/orders/cancel"
ORDER_STATUS_PATH_URL = "/api/v2/peatio/market/orders/{id}"
USER_BALANCES_PATH_URL = "/api/v2/peatio/account/balances"

# Limites de requêtes pour l'AsyncThrottler
RATE_LIMITS = [
    RateLimit(limit_id=CHECK_NETWORK_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=SERVER_TIME_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=EXCHANGE_INFO_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=SNAPSHOT_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=TICKER_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=ORDER_CREATE_PATH_URL, limit=30, time_interval=60),
    RateLimit(limit_id=ORDER_CANCEL_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=ORDER_STATUS_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=USER_BALANCES_PATH_URL, limit=30, time_interval=60),
]