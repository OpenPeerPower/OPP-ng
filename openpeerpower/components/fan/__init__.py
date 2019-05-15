"""Provides functionality to interact with fans."""
from datetime import timedelta
import functools as ft
import logging

import voluptuous as vol

from openpeerpower.components import group
from openpeerpower.const import (SERVICE_TURN_ON, SERVICE_TOGGLE,
                                 SERVICE_TURN_OFF, ATTR_ENTITY_ID)
from openpeerpower.loader import bind_opp
from openpeerpower.helpers.entity import ToggleEntity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.config_validation import (  # noqa
    PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE)
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'fan'
SCAN_INTERVAL = timedelta(seconds=30)

GROUP_NAME_ALL_FANS = 'all fans'
ENTITY_ID_ALL_FANS = group.ENTITY_ID_FORMAT.format(GROUP_NAME_ALL_FANS)

ENTITY_ID_FORMAT = DOMAIN + '.{}'

# Bitfield of features supported by the fan entity
SUPPORT_SET_SPEED = 1
SUPPORT_OSCILLATE = 2
SUPPORT_DIRECTION = 4

SERVICE_SET_SPEED = 'set_speed'
SERVICE_OSCILLATE = 'oscillate'
SERVICE_SET_DIRECTION = 'set_direction'

SPEED_OFF = 'off'
SPEED_LOW = 'low'
SPEED_MEDIUM = 'medium'
SPEED_HIGH = 'high'

DIRECTION_FORWARD = 'forward'
DIRECTION_REVERSE = 'reverse'

ATTR_SPEED = 'speed'
ATTR_SPEED_LIST = 'speed_list'
ATTR_OSCILLATING = 'oscillating'
ATTR_DIRECTION = 'direction'

PROP_TO_ATTR = {
    'speed': ATTR_SPEED,
    'speed_list': ATTR_SPEED_LIST,
    'oscillating': ATTR_OSCILLATING,
    'direction': ATTR_DIRECTION,
}  # type: dict

FAN_SET_SPEED_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_SPEED): cv.string
})  # type: dict

FAN_TURN_ON_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Optional(ATTR_SPEED): cv.string
})  # type: dict

FAN_TURN_OFF_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.comp_entity_ids
})  # type: dict

FAN_OSCILLATE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_OSCILLATING): cv.boolean
})  # type: dict

FAN_TOGGLE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids
})

FAN_SET_DIRECTION_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Optional(ATTR_DIRECTION): cv.string
})  # type: dict


@bind_opp
def is_on(opp, entity_id: str = None) -> bool:
    """Return if the fans are on based on the statemachine."""
    entity_id = entity_id or ENTITY_ID_ALL_FANS
    state = opp.states.get(entity_id)
    return state.attributes[ATTR_SPEED] not in [SPEED_OFF, None]


async def async_setup(opp, config: dict):
    """Expose fan control via statemachine and services."""
    component = opp.data[DOMAIN] = EntityComponent(
        _LOGGER, DOMAIN, opp, SCAN_INTERVAL, GROUP_NAME_ALL_FANS)

    await component.async_setup(config)

    component.async_register_entity_service(
        SERVICE_TURN_ON, FAN_TURN_ON_SCHEMA,
        'async_turn_on'
    )
    component.async_register_entity_service(
        SERVICE_TURN_OFF, FAN_TURN_OFF_SCHEMA,
        'async_turn_off'
    )
    component.async_register_entity_service(
        SERVICE_TOGGLE, FAN_TOGGLE_SCHEMA,
        'async_toggle'
    )
    component.async_register_entity_service(
        SERVICE_SET_SPEED, FAN_SET_SPEED_SCHEMA,
        'async_set_speed'
    )
    component.async_register_entity_service(
        SERVICE_OSCILLATE, FAN_OSCILLATE_SCHEMA,
        'async_oscillate'
    )
    component.async_register_entity_service(
        SERVICE_SET_DIRECTION, FAN_SET_DIRECTION_SCHEMA,
        'async_set_direction'
    )

    return True


async def async_setup_entry(opp, entry):
    """Set up a config entry."""
    return await opp.data[DOMAIN].async_setup_entry(entry)


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.data[DOMAIN].async_unload_entry(entry)


class FanEntity(ToggleEntity):
    """Representation of a fan."""

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        raise NotImplementedError()

    def async_set_speed(self, speed: str):
        """Set the speed of the fan.

        This method must be run in the event loop and returns a coroutine.
        """
        if speed is SPEED_OFF:
            return self.async_turn_off()
        return self.opp.async_add_job(self.set_speed, speed)

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        raise NotImplementedError()

    def async_set_direction(self, direction: str):
        """Set the direction of the fan.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.opp.async_add_job(self.set_direction, direction)

    # pylint: disable=arguments-differ
    def turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn on the fan."""
        raise NotImplementedError()

    # pylint: disable=arguments-differ
    def async_turn_on(self, speed: str = None, **kwargs):
        """Turn on the fan.

        This method must be run in the event loop and returns a coroutine.
        """
        if speed is SPEED_OFF:
            return self.async_turn_off()
        return self.opp.async_add_job(
            ft.partial(self.turn_on, speed, **kwargs))

    def oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        pass

    def async_oscillate(self, oscillating: bool):
        """Oscillate the fan.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.opp.async_add_job(self.oscillate, oscillating)

    @property
    def is_on(self):
        """Return true if the entity is on."""
        return self.speed not in [SPEED_OFF, None]

    @property
    def speed(self) -> str:
        """Return the current speed."""
        return None

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return []

    @property
    def current_direction(self) -> str:
        """Return the current direction of the fan."""
        return None

    @property
    def state_attributes(self) -> dict:
        """Return optional state attributes."""
        data = {}  # type: dict

        for prop, attr in PROP_TO_ATTR.items():
            if not hasattr(self, prop):
                continue

            value = getattr(self, prop)
            if value is not None:
                data[attr] = value

        return data

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return 0
