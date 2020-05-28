"""Provides device automations for ZHA devices that emit events."""
import voluptuous as vol

import openpeerpower.components.automation.event as event
from openpeerpower.components.device_automation import TRIGGER_BASE_SCHEMA
from openpeerpower.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from openpeerpower.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE

from . import DOMAIN
from .core.helpers import async_get_zha_device

CONF_SUBTYPE = "subtype"
DEVICE = "device"
DEVICE_IEEE = "device_ieee"
ZHA_EVENT = "zha_event"

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): str, vol.Required(CONF_SUBTYPE): str}
)


async def async_validate_trigger_config(opp, config):
    """Validate config."""
    config = TRIGGER_SCHEMA(config)

    if "zha" in opp.config.components:
        trigger = (config[CONF_TYPE], config[CONF_SUBTYPE])
        zha_device = await async_get_zha_device(opp, config[CONF_DEVICE_ID])
        if (
            zha_device.device_automation_triggers is None
            or trigger not in zha_device.device_automation_triggers
        ):
            raise InvalidDeviceAutomationConfig

    return config


async def async_attach_trigger(opp, config, action, automation_info):
    """Listen for state changes based on configuration."""
    trigger = (config[CONF_TYPE], config[CONF_SUBTYPE])
    zha_device = await async_get_zha_device(opp, config[CONF_DEVICE_ID])

    trigger = zha_device.device_automation_triggers[trigger]

    event_config = {
        event.CONF_PLATFORM: "event",
        event.CONF_EVENT_TYPE: ZHA_EVENT,
        event.CONF_EVENT_DATA: {DEVICE_IEEE: str(zha_device.ieee), **trigger},
    }

    event_config = event.TRIGGER_SCHEMA(event_config)
    return await event.async_attach_trigger(
        opp, event_config, action, automation_info, platform_type="device"
    )


async def async_get_triggers(opp, device_id):
    """List device triggers.

    Make sure the device supports device automations and
    if it does return the trigger list.
    """
    zha_device = await async_get_zha_device(opp, device_id)

    if not zha_device.device_automation_triggers:
        return

    triggers = []
    for trigger, subtype in zha_device.device_automation_triggers.keys():
        triggers.append(
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_PLATFORM: DEVICE,
                CONF_TYPE: trigger,
                CONF_SUBTYPE: subtype,
            }
        )

    return triggers
