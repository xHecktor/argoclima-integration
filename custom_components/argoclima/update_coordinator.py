import logging
from datetime import timedelta

from custom_components.argoclima.api import ArgoApiClient
from custom_components.argoclima.const import DOMAIN
from custom_components.argoclima.data import ArgoData
from custom_components.argoclima.device_type import ArgoDeviceType
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed


_LOGGER: logging.Logger = logging.getLogger(__package__)

# Number of consecutive failed polls tolerated before the device
# is marked unavailable. Argo units occasionally drop single requests.
MAX_FAILED_UPDATES = 3


class ArgoDataUpdateCoordinator(DataUpdateCoordinator[ArgoData]):
    def __init__(
        self, hass: HomeAssistant, client: ArgoApiClient, type: ArgoDeviceType
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=type.update_interval),
            update_method=self._async_update,
        )

        self._api = client
        self._failed_updates = 0
        self.platforms = []
        self.data = ArgoData(type)

    async def _async_update(self) -> ArgoData:
        """Update data via library."""
        try:
            data = await self._api.async_sync_data(self.data)
        except Exception as exception:
            self._failed_updates += 1
            if self._failed_updates >= MAX_FAILED_UPDATES:
                raise UpdateFailed(
                    f"Update failed {self._failed_updates} times in a row: {exception}"
                ) from exception
            _LOGGER.debug(
                "Update failed (%d/%d), keeping last known data: %s",
                self._failed_updates,
                MAX_FAILED_UPDATES,
                exception,
            )
            return self.data
        self._failed_updates = 0
        return data
