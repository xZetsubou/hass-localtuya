"""Class to perform requests to Tuya Cloud APIs."""

import asyncio
import json
import logging
import time

from tuya_sharing import CustomerApi
from tuya_sharing.customerapi import CustomerTokenInfo

from homeassistant.core import HomeAssistant

DEVICES_UPDATE_INTERVAL = 300
DEVICES_UPDATE_INTERVAL_FORCED = 10

class CustomAdapter(logging.LoggerAdapter):
    """Adapter logger for cloud api."""

    def process(self, msg, kwargs):
        return f"[{self.extra.get('prefix', '')}] {msg}", kwargs

class TuyaCloudApi:
    """Class to send API calls."""

    def __init__(self, 
        hass: HomeAssistant,
        client_id: str,
        user_code: str,
        terminal_id: str,
        end_point: str,
        token_response: dict[str, Any] = None,
    ):
        """Initialize the class."""
        self._logger = CustomAdapter(
            logging.getLogger(__name__), {"prefix": user_code[:3] + "..." + user_code[-3:]}
        )
        self.hass = hass
        self.customer_api = CustomerApi(
            CustomerTokenInfo(token_response),
            client_id,
            user_code,
            end_point,
            None
        )

        self._client_id = client_id

        self.device_list = {}
        self.cached_device_list = {}

        self._last_devices_update = int(time.time())

    async def async_make_request(self, method, url, body=None, params={}):
        """Perform requests."""
        try:
            if method == "GET":
                return await self.hass.async_add_executor_job(self.customer_api.get, url, params)
            else:
                raise NotImplemented()
        except (TimeoutError,OSError) as ex:
            self._logger.debug(f"Failed to send request to tuya cloud: {ex}")
            return False

    async def _query_homes(self) -> list[str]:
        response = await self.async_make_request("GET", f"/v1.0/m/life/users/homes")

        if response and response.get("success", False):
            _homes = []
            for home in response["result"]:
                _home = str(home["ownerId"])
                _homes.append(_home)
            return _homes

        return []

    async def async_get_devices_list(self, force_update=False) -> str | None:
        """Obtain the list of devices associated to a user. - force_update will ignore last update check."""
        interval = (
            DEVICES_UPDATE_INTERVAL_FORCED if force_update else DEVICES_UPDATE_INTERVAL
        )
        if (
            self.device_list
            and int(time.time()) - (self._last_devices_update + interval) < 0
        ):
            return self._logger.debug(f"Devices has been updated a minutes ago.")

        for home_id in await self._query_homes():
            if not (
                resp := await self.async_make_request(
                    "GET", url=f"/v1.0/m/life/ha/home/devices", params={"homeId": home_id}
                )
            ):
                return self._logger.debug(f"Failed to retrieve a devices list")

            if not resp["success"]:
                return f"Error {resp['code']}: {resp['msg']}"

            self.device_list.update({dev["id"]: dev for dev in resp["result"]})

        self._last_devices_update = int(time.time())
        return "ok"

    async def async_get_devices_dps_query(self):
        """Update All the devices dps_data."""
        # Get Devices DPS Data.
        await asyncio.wait(
            asyncio.create_task(self.async_get_device_functions(devid))
            for devid in self.device_list
        )
        return "ok"

    async def async_get_device_specifications(self, device_id) -> dict[str, dict]:
        """Obtain the DP ID mappings for a device."""

        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v1.1/devices/{device_id}/specifications"
            )
        ):
            return self._logger.debug(f"Failed to retrieve a device specifications")

        if not resp["success"]:
            return {}, f"Error {resp['code']}: {resp['msg']}"

        return resp["result"], "ok"

    async def async_get_device_query_properties(self, device_id) -> dict[dict, str]:
        """Obtain the DP ID mappings for a device correctly! Note: This won't works if the subscription expired."""

        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v2.0/cloud/thing/{device_id}/shadow/properties"
            )
        ):
            return self._logger.debug(f"Failed to retrieve a device properties")

        if not resp["success"]:
            return {}, f"Error {resp['code']}: {resp['msg']}"

        return resp["result"], "ok"

    async def async_get_device_query_things_data_model(
        self, device_id
    ) -> dict[str, dict]:
        """Obtain the DP ID mappings for a device."""

        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v2.0/cloud/thing/{device_id}/model"
            )
        ):
            return self._logger.debug(f"Failed to retrieve a device data model")

        if not resp["success"]:
            return {}, f"Error {resp['code']}: {resp['msg']}"

        return resp["result"], "ok"

    async def async_get_device_functions(self, device_id) -> dict[str, dict]:
        """Pull Devices Properties and Specifications to devices_list"""
        cached = device_id in self.cached_device_list
        if cached and (dps_data := self.cached_device_list[device_id].get("dps_data")):
            self.device_list[device_id]["dps_data"] = dps_data
            return dps_data

        device_data = {}
        get_data = [
            self.async_get_device_specifications(device_id),
            self.async_get_device_query_properties(device_id),
            self.async_get_device_query_things_data_model(device_id),
        ]
        try:
            specs, query_props, query_model = await asyncio.gather(*get_data)
        except (Exception,) as ex:
            self._logger.debug(f"Failed to get DPS functions for {device_id} - {ex}")
            return

        if query_props[1] == "ok":
            device_data = {str(p["dp_id"]): p for p in query_props[0].get("properties")}
        if specs[1] == "ok":
            for func in specs[0].get("functions", {}):
                if str(func.get("dp_id")) in device_data:
                    device_data[str(func["dp_id"])].update(func)
                elif dp_id := func.get("dp_id"):
                    device_data[str(dp_id)] = func
        if query_model[1] == "ok":
            model_data = json.loads(query_model[0]["model"])
            services = model_data.get("services", [{}])[0]
            properties = services.get("properties")
            for dp_data in properties if properties else {}:
                refactored = {
                    "id": dp_data.get("abilityId"),
                    # "code": dp_data.get("code"),
                    "accessMode": dp_data.get("accessMode"),
                    # values: json.loads later
                    "values": str(dp_data.get("typeSpec")).replace("'", '"'),
                }
                if str(dp_data["abilityId"]) in device_data:
                    device_data[str(dp_data["abilityId"])].update(refactored)
                else:
                    refactored["code"] = dp_data.get("code")
                    device_data[str(dp_data["abilityId"])] = refactored

        if "28841002" in str(query_props[1]):
            # No permissions This affect auto configure feature.
            self.device_list[device_id]["localtuya_note"] = str(query_props[1])

        if device_data:
            self.device_list[device_id]["dps_data"] = device_data
            self.cached_device_list.update({device_id: self.device_list[device_id]})

        return device_data

    async def async_connect(self):
        """Connect to cloudAPI"""
        if (res := await self.async_get_devices_list()) and res != "ok":
            self._logger.warning("Cloud API connection failed: %s", res)
            return "device_list_failed", res
        if res:
            self._logger.info("Cloud API connection succeeded.")
        return True, res
