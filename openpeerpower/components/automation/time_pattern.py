"""Offer time listening automation rules."""
import logging

import voluptuous as vol

from openpeerpower.const import CONF_PLATFORM
from openpeerpower.core import callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.event import async_track_time_change

# mypy: allow-untyped-defs, no-check-untyped-defs

CONF_HOURS = "hours"
CONF_MINUTES = "minutes"
CONF_SECONDS = "seconds"

_LOGGER = logging.getLogger(__name__)

TRIGGER_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(CONF_PLATFORM): "time_pattern",
            CONF_HOURS: vol.Any(vol.Coerce(int), vol.Coerce(str)),
            CONF_MINUTES: vol.Any(vol.Coerce(int), vol.Coerce(str)),
            CONF_SECONDS: vol.Any(vol.Coerce(int), vol.Coerce(str)),
        }
    ),
    cv.has_at_least_one_key(CONF_HOURS, CONF_MINUTES, CONF_SECONDS),
)


async def async_attach_trigger(opp, config, action, automation_info):
    """Listen for state changes based on configuration."""
    hours = config.get(CONF_HOURS)
    minutes = config.get(CONF_MINUTES)
    seconds = config.get(CONF_SECONDS)

    # If larger units are specified, default the smaller units to zero
    if minutes is None and hours is not None:
        minutes = 0
    if seconds is None and minutes is not None:
        seconds = 0

    @callback
    def time_automation_listener(now):
        """Listen for time changes and calls action."""
        opp.async_run_job(action, {"trigger": {"platform": "time_pattern", "now": now}})

    return async_track_time_change(
        opp, time_automation_listener, hour=hours, minute=minutes, second=seconds
    )
