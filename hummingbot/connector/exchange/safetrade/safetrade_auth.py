import hmac
import hashlib
import time
from typing import Any, Dict
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest

class SafetradeAuth(AuthBase):
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key.encode("utf-8")

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        nonce = str(int(time.time() * 1000))
        verb = request.method.value.upper()
        path = request.url.split(REST_URL)[-1]
        
        # Encodage des paramètres dans l'ordre alphabétique
        payload_str = ""
        if request.params:
            payload_str = "&".join(f"{k}={request.params[k]}" for k in sorted(request.params.keys()))
        elif request.data:
            payload_str = request.data if isinstance(request.data, str) else ""

        message = f"{verb}|{path}|{nonce}|{payload_str}".encode("utf-8")
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()

        headers = request.headers or {}
        headers.update({
            "X-Auth-Apikey": self.api_key,
            "X-Auth-Nonce": nonce,
            "X-Auth-Signature": signature,
            "Content-Type": "application/json"
        })
        request.headers = headers
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        return request