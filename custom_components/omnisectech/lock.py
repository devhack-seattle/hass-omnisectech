"""Platform for lock integration."""
from __future__ import annotations

import logging

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.lock import (PLATFORM_SCHEMA, LockEntity)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

import requests

from enum import IntEnum

from .auth import OmniSecTechAuth

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    # vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    # breakpoint()
    config = config_entry.data
    # config = hass.data[DOMAIN][config_entry.entry_id]

    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]

    async_add_entities([Door(username, password)], True)


class Door(LockEntity):
    _attr_assumed_state = True
    _attr_has_entity_name = True

    class DoorStates(IntEnum):
        ACTION_UNLOCK=1
        ACTION_LOCK=2
        ACTION_REMAIN_UNLOCKED = 3
        ACTION_REMAIN_LOCKED = 4 # DO NOT USE

    def __init__(self, username, password):
        self._auth = OmniSecTechAuth(username, password)
        self._is_locked = True
        self._is_lockdown = False

        self._attr_unique_id = "wasdwasd"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            name=self.name,
            # manufacturer=self.lock.manufacturername,
            # model=self.lock.productname,
            # sw_version=self.lock.swversion,
            # via_device=(DOMAIN, self.api.bridgeid),
        )

    @property
    def name(self):
        return "Door lock"
    
    @property
    def is_locked(self):
        return self._is_locked

    @property
    def is_lockdown(self):
        return self._is_lockdown

    def update(self, **kwargs):
        # TODO: implement polling. does the web frontend do this through websockets?
        return NotImplemented

    def unlock(self, **kwargs):
        """Unlock the front door"""
        self.request(self.DoorStates.ACTION_REMAIN_UNLOCKED)
        self._is_locked = False
        self._is_lockdown = False

    def lock(self, **kwargs):
        """Lock the front door"""
        self.request(self.DoorStates.ACTION_LOCK)
        self._is_locked = True
        self._is_lockdown = False

    def lockdown(self, **kwargs):
        """Lock the front door and disable keycode / relay access"""
        self.request(self.DoorStates.ACTION_REMAIN_LOCKED)
        self._is_locked = True
        self._is_lockdown = True

    def request(self, action):
        data = {
            "DoorElementOperation": {
                "Action": action,
                "Direction": 0,  # not sure what this is
            }
        }
        # TODO: don't hardcode door ID
        url = "https://server.omnisectech.com:2580/ISAPI/Bumblebee/ACSPlugin/V0/RemoteControl/DoorElements/8299/Control?MT=PUT"
        r = requests.post(
            url,
            params={"MT": "PUT"},
            json=data,
            auth=self._auth,
            verify=False,
        )
        if r.json()["ResponseStatus"]["ErrorCode"] != 0:
            raise Exception(r.json())

        print(r.json())
        print(r)
