from hummingbot.core.api_throttler.data_types import RateLimit

DEFAULT_DOMAIN = "safe_trade"

# URLs
REST_URL = "https://safe.trade"
WSS_PUBLIC_URL = "wss://safe.trade/api/v2/ranger/public"
WSS_PRIVATE_URL = "wss://safe.trade/api/v2/ranger/private"

# Endpoints Peatio v2
DEPTH_PATH_URL = "/api/v2/peatio/public/markets/{market}/depth-merged"
SNAPSHOT_PATH_URL = "/api/v2/peatio/public/markets/{market}/depth"
SERVER_TIME_PATH_URL = "/api/v2/peatio/public/timestamp"
EXCHANGE_INFO_PATH_URL = "/api/v2/peatio/public/markets"

CREATE_ORDER_PATH_URL = "/api/v2/peatio/market/orders"
CANCEL_ORDER_PATH_URL = "/api/v2/peatio/market/orders/cancel"
GET_ACCOUNT_PATH_URL = "/api/v2/peatio/account/balances"

# Limites API (ex: 60 requêtes/minute)
RATE_LIMITS = [
    RateLimit(limit_id=EXCHANGE_INFO_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=DEPTH_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=CREATE_ORDER_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=CANCEL_ORDER_PATH_URL, limit=60, time_interval=60),
    RateLimit(limit_id=GET_ACCOUNT_PATH_URL, limit=60, time_interval=60),
]