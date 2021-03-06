"""The tests for Climate device triggers."""
import pytest
import voluptuous_serialize

import openpeerpower.components.automation as automation
from openpeerpower.components.climate import DOMAIN, const, device_trigger
from openpeerpower.helpers import config_validation as cv, device_registry
from openpeerpower.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)


@pytest.fixture
def device_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def entity_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_registry(opp)


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def test_get_triggers(opp, device_reg, entity_reg):
    """Test we get the expected triggers from a climate device."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_opp(opp)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    entity_id = f"{DOMAIN}.test_5678"
    opp.states.async_set(
        entity_id,
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_ACTION: const.CURRENT_HVAC_IDLE,
            const.ATTR_CURRENT_HUMIDITY: 23,
            const.ATTR_CURRENT_TEMPERATURE: 18,
        },
    )
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "hvac_mode_changed",
            "device_id": device_entry.id,
            "entity_id": entity_id,
        },
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "current_temperature_changed",
            "device_id": device_entry.id,
            "entity_id": entity_id,
        },
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "current_humidity_changed",
            "device_id": device_entry.id,
            "entity_id": entity_id,
        },
    ]
    triggers = await async_get_device_automations(opp, "trigger", device_entry.id)
    assert_lists_same(triggers, expected_triggers)


async def test_if_fires_on_state_change(opp, calls):
    """Test for turn_on and turn_off triggers firing."""
    opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_COOL,
        {
            const.ATTR_HVAC_ACTION: const.CURRENT_HVAC_IDLE,
            const.ATTR_CURRENT_HUMIDITY: 23,
            const.ATTR_CURRENT_TEMPERATURE: 18,
        },
    )

    assert await async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": "climate.entity",
                        "type": "hvac_mode_changed",
                        "to": const.HVAC_MODE_AUTO,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "hvac_mode_changed"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": "climate.entity",
                        "type": "current_temperature_changed",
                        "above": 20,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "current_temperature_changed"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": "climate.entity",
                        "type": "current_humidity_changed",
                        "below": 10,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "current_humidity_changed"},
                    },
                },
            ]
        },
    )

    # Fake that the HVAC mode is changing
    opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_AUTO,
        {
            const.ATTR_HVAC_ACTION: const.CURRENT_HVAC_COOL,
            const.ATTR_CURRENT_HUMIDITY: 23,
            const.ATTR_CURRENT_TEMPERATURE: 18,
        },
    )
    await opp.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "hvac_mode_changed"

    # Fake that the temperature is changing
    opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_AUTO,
        {
            const.ATTR_HVAC_ACTION: const.CURRENT_HVAC_COOL,
            const.ATTR_CURRENT_HUMIDITY: 23,
            const.ATTR_CURRENT_TEMPERATURE: 23,
        },
    )
    await opp.async_block_till_done()
    assert len(calls) == 2
    assert calls[1].data["some"] == "current_temperature_changed"

    # Fake that the humidity is changing
    opp.states.async_set(
        "climate.entity",
        const.HVAC_MODE_AUTO,
        {
            const.ATTR_HVAC_ACTION: const.CURRENT_HVAC_COOL,
            const.ATTR_CURRENT_HUMIDITY: 7,
            const.ATTR_CURRENT_TEMPERATURE: 23,
        },
    )
    await opp.async_block_till_done()
    assert len(calls) == 3
    assert calls[2].data["some"] == "current_humidity_changed"


async def test_get_trigger_capabilities_hvac_mode(opp):
    """Test we get the expected capabilities from a climate trigger."""
    capabilities = await device_trigger.async_get_trigger_capabilities(
        opp,
        {
            "platform": "device",
            "domain": "climate",
            "type": "hvac_mode_changed",
            "entity_id": "climate.upstairs",
            "to": "heat",
        },
    )
    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [{"name": "for", "optional": True, "type": "positive_time_period_dict"}]


@pytest.mark.parametrize(
    "type", ["current_temperature_changed", "current_humidity_changed"]
)
async def test_get_trigger_capabilities_temp_humid(opp, type):
    """Test we get the expected capabilities from a climate trigger."""
    capabilities = await device_trigger.async_get_trigger_capabilities(
        opp,
        {
            "platform": "device",
            "domain": "climate",
            "type": "current_temperature_changed",
            "entity_id": "climate.upstairs",
            "above": "23",
        },
    )

    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "description": {"suffix": "°C"},
            "name": "above",
            "optional": True,
            "type": "float",
        },
        {
            "description": {"suffix": "°C"},
            "name": "below",
            "optional": True,
            "type": "float",
        },
        {"name": "for", "optional": True, "type": "positive_time_period_dict"},
    ]
