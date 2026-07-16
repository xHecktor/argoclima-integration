import asyncio
import logging

import aiohttp
import async_timeout
from custom_components.argoclima.data import ArgoData
from custom_components.argoclima.device_type import ArgoDeviceType

TIMEOUT = 15

HEADERS = {
    "Content-type": "text/html",
    "User-Agent": "HomeAssistant-Argoclima/1.2.0",
}

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ArgoApiClient:
    def __init__(
        self, type: ArgoDeviceType, host: str, session: aiohttp.ClientSession
    ) -> None:
        self._host = host
        self._port = type.port
        self._type = type
        self._session = session
        self._lock = asyncio.Lock()

    async def async_sync_data(self, data: ArgoData) -> ArgoData:
        if data is None:
            data = ArgoData(self._type)

        url = f"http://{self._host}:{self._port}/?HMI={data.to_parameter_string()}&UPD={1 if data.is_update_pending() else 0}"

        async with self._lock, async_timeout.timeout(TIMEOUT):
            _LOGGER.debug("Requesting %s", url)
            response = await self._session.get(url, headers=HEADERS)
            text = await response.text()
            _LOGGER.debug("Response from %s: %s", self._host, text)
            data.parse_response_parameter_string(text)
            return data
